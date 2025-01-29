from app import db
from app.models import Task, GlobalCounter

def test_sync_tasks(client, add_user, login):
    """Test the sync_tasks route with various scenarios."""
    # Add test users
    ambulance_user = add_user('ambulance_user', 'password123', 'ambulance')
    ambulance_token = login('ambulance_user', 'password123')
    headers = {'Authorization': f'Bearer {ambulance_token}'}

    # Initialize GlobalCounter
    counter = GlobalCounter.query.first()
    if not counter:
        counter = GlobalCounter(task_counter=0)
        db.session.add(counter)
        db.session.commit()
    initial_version = counter.task_counter

    # Test 1: Initial sync with empty database
    response = client.get(f'/api/tasks/sync?version={initial_version}', headers=headers)
    assert response.status_code == 304  # No changes, so return 304

    # Test 2: Create a task and verify sync
    task_data = {
        'title': 'Test Task 1',
        'description': 'First test task',
        'location': {
            'latitude': 12.345678,
            'longitude': 98.765432
        }
    }
    create_response = client.post('/api/tasks', json=task_data, headers=headers)
    assert create_response.status_code == 201
    task1_id = create_response.json['data']['task_id']

    # Sync with old version
    response = client.get(f'/api/tasks/sync?version={initial_version}', headers=headers)
    assert response.status_code == 200  # Changes exist, return 200
    response_data = response.json
    assert 'data' in response_data
    data = response_data['data']
    assert data['version'] > initial_version
    assert data['needs_sync'] is True
    assert len(data['tasks']) == 1
    assert data['tasks'][0]['id'] == task1_id

    # Test 3: Sync with current version (no changes)
    current_version = data['version']
    response = client.get(f'/api/tasks/sync?version={current_version}', headers=headers)
    assert response.status_code == 304  # No changes since last sync

    # Test 4: Add another task and verify sync
    task_data = {
        'title': 'Test Task 2',
        'description': 'Second test task',
        'location': {
            'latitude': 23.456789,
            'longitude': 87.654321
        }
    }
    create_response = client.post('/api/tasks', json=task_data, headers=headers)
    assert create_response.status_code == 201
    task2_id = create_response.json['data']['task_id']

    # Sync with previous version
    response = client.get(f'/api/tasks/sync?version={current_version}', headers=headers)
    assert response.status_code == 200  # Changes exist
    response_data = response.json
    assert 'data' in response_data
    data = response_data['data']
    assert data['version'] > current_version
    assert data['needs_sync'] is True
    assert len(data['tasks']) == 2
    task_ids = [task['id'] for task in data['tasks']]
    assert task1_id in task_ids
    assert task2_id in task_ids

    # Test 5: Test with invalid version parameter
    response = client.get('/api/tasks/sync?version=invalid', headers=headers)
    assert response.status_code == 200  # Treats invalid version as 0
    response_data = response.json
    assert 'data' in response_data
    data = response_data['data']
    assert data['needs_sync'] is True
    assert len(data['tasks']) == 2

    # Test 6: Test without version parameter
    response = client.get('/api/tasks/sync', headers=headers)
    assert response.status_code == 200  # Treats missing version as 0
    response_data = response.json
    assert 'data' in response_data
    data = response_data['data']
    assert data['needs_sync'] is True
    assert len(data['tasks']) == 2

    # Test 7: Verify authentication requirement
    response = client.get('/api/tasks/sync')
    assert response.status_code == 401  # Unauthorized 
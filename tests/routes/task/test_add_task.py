from app import db
from app.models import Task, TaskLog

def test_add_task(client, add_user, login):
    """Test the add_task route with various scenarios."""
    # Add users
    ambulance_user = add_user('ambulance_user', 'password123', 'ambulance')
    admin_user = add_user('admin_user', 'password123', 'admin')
    unauthorized_user = add_user('unauthorized_user', 'password123', 'guest')

    ambulance_token = login('ambulance_user', 'password123')
    admin_token = login('admin_user', 'password123')

    # Test case 1: Successful task creation by ambulance
    task_data = {
        'title': 'Ambulance Task',
        'description': 'Created by ambulance.',
        'location': {
            'latitude': 12.345678,
            'longitude': 98.765432
        }
    }
    response = client.post('/api/tasks', json=task_data, headers={
        'Authorization': f'Bearer {ambulance_token}'
    })
    assert response.status_code == 201
    response_data = response.json
    assert 'message' in response_data
    assert response_data['message'] == 'Task created successfully'
    assert 'data' in response_data
    assert 'task_id' in response_data['data']

    # Verify task in database
    task_id = response_data['data']['task_id']
    task = db.session.get(Task, task_id)
    assert task is not None
    assert task.title == task_data['title']
    assert task.description == task_data['description']
    assert task.location_lat == task_data['location']['latitude']
    assert task.location_lon == task_data['location']['longitude']
    assert task.created_by == ambulance_user.id
    assert task.assigned_to == ambulance_user.id

    # Test case 2: Missing required fields
    response = client.post('/api/tasks', json={}, headers={
        'Authorization': f'Bearer {ambulance_token}'
    })
    assert response.status_code == 400
    assert 'Missing required fields' in response.json['message']

    # Test case 3: Missing location details
    invalid_data = {
        'title': 'Task with Missing Location',
        'location': {'latitude': 12.345678}
    }
    response = client.post('/api/tasks', json=invalid_data, headers={
        'Authorization': f'Bearer {ambulance_token}'
    })
    assert response.status_code == 400
    assert 'Missing location details' in response.json['message']

    # Test case 4: Unauthorized user
    unauthorized_token = login('unauthorized_user', 'password123')
    response = client.post('/api/tasks', json=task_data, headers={
        'Authorization': f'Bearer {unauthorized_token}'
    })
    assert response.status_code == 403
    assert 'Access denied' in response.json['message']

    # Test case 5: Admin assigns task to another user
    admin_task_data = {
        'title': 'Admin Task',
        'description': 'Assigned by admin.',
        'location': {
            'latitude': 23.456789,
            'longitude': 87.654321
        },
        'assigned_to': ambulance_user.id
    }
    response = client.post('/api/tasks', json=admin_task_data, headers={
        'Authorization': f'Bearer {admin_token}'
    })
    assert response.status_code == 201
    response_data = response.json
    assert response_data['message'] == 'Task created successfully'
    assert 'data' in response_data
    assert 'task_id' in response_data['data']

    # Verify admin-assigned task in database
    task_id = response_data['data']['task_id']
    task = db.session.get(Task, task_id)
    assert task is not None
    assert task.assigned_to == ambulance_user.id

    # Verify task log entry
    task_log = TaskLog.query.filter_by(task_id=task_id).first()
    assert task_log is not None
    assert task_log.status == 'new'
    assert task_log.assigned_to == ambulance_user.id
    assert f'Task created by admin {admin_user.id}' in task_log.note 
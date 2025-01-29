from app import db
from app.models import TaskLog

def test_get_task_logs(client, add_user, login):
    """Test the get_task_logs route for a specific task, including additional manually added logs."""
    # Add test users
    ambulance_user = add_user('ambulance_user', 'password123', 'ambulance')
    ambulance_token = login('ambulance_user', 'password123')

    # Create a test task
    task_data = {
        'title': 'Test Task',
        'description': 'Task for log testing.',
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
    assert 'data' in response_data
    task_id = response_data['data']['task_id']

    # Verify the automatically created log
    response = client.get(f'/api/tasks/{task_id}/logs', headers={
        'Authorization': f'Bearer {ambulance_token}'
    })
    assert response.status_code == 200
    response_data = response.json
    assert 'data' in response_data
    logs = response_data['data']
    assert len(logs) == 1  # Only one log should exist for task creation

    # Verify initial log
    assert logs[0]['status'] == 'new'
    assert logs[0]['note'] == f"Task created by ambulance {ambulance_user.id}"
    assert logs[0]['task_id'] == task_id
    assert logs[0]['assigned_to'] == ambulance_user.id
    assert logs[0]['modified_by'] == ambulance_user.id

    # Manually add additional logs
    log_1 = TaskLog(
        task_id=task_id,
        status='in_progress',
        assigned_to=ambulance_user.id,
        modified_by=ambulance_user.id,
        note='Task started.'
    )
    log_2 = TaskLog(
        task_id=task_id,
        status='completed',
        assigned_to=ambulance_user.id,
        modified_by=ambulance_user.id,
        note='Task completed successfully.'
    )
    db.session.add_all([log_1, log_2])
    db.session.commit()

    # Fetch the task logs again to verify additional logs
    response = client.get(f'/api/tasks/{task_id}/logs', headers={
        'Authorization': f'Bearer {ambulance_token}'
    })
    assert response.status_code == 200
    response_data = response.json
    assert 'data' in response_data
    logs = response_data['data']
    assert len(logs) == 3  # One auto-created log + two manually added logs

    # Verify logs (in reverse chronological order)
    assert logs[0]['status'] == 'completed'
    assert logs[0]['note'] == 'Task completed successfully.'
    
    assert logs[1]['status'] == 'in_progress'
    assert logs[1]['note'] == 'Task started.'
    
    assert logs[2]['status'] == 'new'
    assert logs[2]['note'] == f"Task created by ambulance {ambulance_user.id}"

    # Test logs for a non-existent task
    response = client.get('/api/tasks/9999/logs', headers={
        'Authorization': f'Bearer {ambulance_token}'
    })
    assert response.status_code == 404
    assert 'Task with ID 9999 not found' in response.json['message'] 
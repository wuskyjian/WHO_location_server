from app import db
from app.models import TaskLog, Task
from datetime import datetime

def test_get_all_tasks(client, add_user, login):
    """Test the get_all_tasks route."""
    # Add test users
    ambulance_user = add_user('ambulance_user', 'password123', 'ambulance')
    admin_user = add_user('admin_user', 'password123', 'admin')

    # Get tokens
    ambulance_token = login('ambulance_user', 'password123')
    admin_token = login('admin_user', 'password123')

    # Create test tasks
    task_data = [
        {
            'title': 'Task 1',
            'description': 'First task.',
            'location': {
                'latitude': 12.345678,
                'longitude': 98.765432
            }
        },
        {
            'title': 'Task 2',
            'description': 'Second task.',
            'assigned_to': ambulance_user.id,
            'location': {
                'latitude': 23.456789,
                'longitude': 87.654321
            }
        }
    ]

    # Create tasks with different users
    headers_ambulance = {'Authorization': f'Bearer {ambulance_token}'}
    headers_admin = {'Authorization': f'Bearer {admin_token}'}
    
    response = client.post('/api/tasks', json=task_data[0], headers=headers_ambulance)
    assert response.status_code == 201
    task1_id = response.json['data']['task_id']  # 从 data 字段获取 task_id
    
    response = client.post('/api/tasks', json=task_data[1], headers=headers_admin)
    assert response.status_code == 201
    task2_id = response.json['data']['task_id']  # 从 data 字段获取 task_id

    # Test getting all tasks as admin
    response = client.get('/api/tasks', headers=headers_admin)
    assert response.status_code == 200
    response_data = response.json
    
    assert 'data' in response_data
    tasks = response_data['data']  # 从 data 字段获取任务列表
    assert len(tasks) == 2
    assert isinstance(tasks, list)
    
    # Verify task details
    for task in tasks:
        assert isinstance(task, dict)
        assert all(key in task for key in [
            'id', 'title', 'description', 'status', 
            'location', 'created_by', 'assigned_to',
            'created_at', 'updated_at'
        ])
        
        if task['id'] == task1_id:
            assert task['title'] == 'Task 1'
            assert task['description'] == 'First task.'
            assert task['created_by'] == ambulance_user.id
            assert task['status'] == 'new'
            assert task['location'] == {
                'latitude': 12.345678,
                'longitude': 98.765432
            }
        else:
            assert task['title'] == 'Task 2'
            assert task['description'] == 'Second task.'
            assert task['created_by'] == admin_user.id
            assert task['assigned_to'] == ambulance_user.id
            assert task['status'] == 'new'
            assert task['location'] == {
                'latitude': 23.456789,
                'longitude': 87.654321
            }

    # Test getting all tasks as ambulance user
    response = client.get('/api/tasks', headers=headers_ambulance)
    assert response.status_code == 200
    response_data = response.json
    assert 'data' in response_data
    tasks = response_data['data']  # 从 data 字段获取任务列表
    assert len(tasks) == 2  # Ambulance users can see all tasks too

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
    task_id = response.json['data']['task_id']  

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

def test_get_task_details(client, add_user, login):
    """Test getting single task details, including error cases."""
    # Create test users
    ambulance_user = add_user('ambulance_user', 'password123', 'ambulance')
    cleaning_user = add_user('cleaning_user', 'password123', 'cleaning_team')
    
    # Login ambulance user
    ambulance_token = login('ambulance_user', 'password123')
    headers = {'Authorization': f'Bearer {ambulance_token}'}
    
    # Test 1: Try to get nonexistent task first
    response = client.get('/api/tasks/99999', headers=headers)
    assert response.status_code == 404
    assert 'Task not found' in response.json['message']
    
    # Test 2: Create and get a real task
    task_data = {
        'title': 'Test Task',
        'description': 'Test Description',
        'location': {
            'latitude': 40.7128,
            'longitude': -74.0060
        }
    }
    
    # Create task
    response = client.post('/api/tasks', json=task_data, headers=headers)
    assert response.status_code == 201
    task_id = response.json['data']['task_id']
    
    # Add some task logs
    task = db.session.get(Task, task_id)
    log1 = TaskLog(
        task_id=task.id,
        status='new',
        assigned_to=cleaning_user.id,
        modified_by=ambulance_user.id,
        note='Initial assignment'
    )
    log2 = TaskLog(
        task_id=task.id,
        status='in_progress',
        assigned_to=cleaning_user.id,
        modified_by=cleaning_user.id,
        note='Started working'
    )
    task.logs.append(log1)
    task.logs.append(log2)
    db.session.add(task)
    db.session.commit()

    # Get task details
    response = client.get(f'/api/tasks/{task_id}', headers=headers)
    
    # Verify response
    assert response.status_code == 200
    data = response.json['data']
    
    # Verify task data
    task = data['task']
    assert task['id'] == task_id
    assert task['title'] == task_data['title']
    assert task['description'] == task_data['description']
    assert task['status'] == 'new'
    assert task['location'] == task_data['location']
    assert task['created_by'] == ambulance_user.id
    assert 'created_at' in task
    assert 'updated_at' in task
    
    # Verify logs
    logs = task['logs']
    assert len(logs) == 3  # 1 auto-generated + 2 manual logs
    
    # Verify log order (most recent first)
    assert logs[0]['status'] == 'in_progress'
    assert logs[0]['note'] == 'Started working'
    
    assert logs[1]['status'] == 'new'
    assert logs[1]['note'] == 'Initial assignment'
    
    assert logs[2]['status'] == 'new'
    assert logs[2]['note'] == f'Task created by ambulance {ambulance_user.id}'


from app import db
from app.models import Task, TaskLog

def test_update_task_ambulance(client, add_user, add_task, login):
    """Test the update_task route for an 'ambulance' role."""
    # Add test users
    ambulance_user = add_user('ambulance_user', 'password123', 'ambulance')
    other_ambulance = add_user('other_ambulance', 'password123', 'ambulance')
    
    # Login as ambulance user
    ambulance_token = login('ambulance_user', 'password123')
    other_token = login('other_ambulance', 'password123')
    
    # Create a test task
    task = add_task(
        created_by=ambulance_user.id,
        assigned_to=ambulance_user.id,
        status='new',
        title='Test Task'
    )

    headers = {'Authorization': f'Bearer {ambulance_token}'}
    other_headers = {'Authorization': f'Bearer {other_token}'}

    # Test 1: Cannot update task without note
    response = client.patch(
        f'/api/tasks/{task.id}',
        json={},
        headers=headers
    )
    assert response.status_code == 400
    assert "Note is required" in response.json['message']

    # Test 2: Cannot modify other user's task
    response = client.patch(
        f'/api/tasks/{task.id}',
        json={'note': 'Test note'},
        headers=other_headers
    )
    assert response.status_code == 403
    assert "Access denied" in response.json['message']

    # Test 3: Cannot modify completed task
    completed_task = add_task(
        created_by=ambulance_user.id,
        assigned_to=ambulance_user.id,
        status='completed',
        title='Completed Task'
    )
    response = client.patch(
        f'/api/tasks/{completed_task.id}',
        json={'note': 'Test note'},
        headers=headers
    )
    assert response.status_code == 403
    assert "Cannot modify completed tasks" in response.json['message']

    # Test 4: Successful note addition
    response = client.patch(
        f'/api/tasks/{task.id}',
        json={'note': 'Added a note to my task'},
        headers=headers
    )
    assert response.status_code == 200
    response_data = response.json
    assert "Task updated successfully" in response_data['message']
    assert 'data' in response_data
    assert 'task' in response_data['data']
    
    # Verify task and log in database
    updated_task = db.session.get(Task, task.id)
    assert updated_task.status == 'new'  # Status should not change
    
    # Verify log was created
    logs = TaskLog.query.filter_by(task_id=task.id).order_by(TaskLog.timestamp.desc()).all()
    assert len(logs) > 0
    latest_log = logs[0]
    assert latest_log.note == 'Added a note to my task'
    assert latest_log.modified_by == ambulance_user.id
    assert latest_log.status == 'new'

def test_update_task_cleaning_team(client, add_user, add_task, login):
    """Test the update_task route for a 'cleaning_team' role."""
    # Add test users
    cleaning_user = add_user('cleaning_user', 'password123', 'cleaning_team')
    other_cleaner = add_user('other_cleaner', 'password123', 'cleaning_team')
    
    # Get tokens
    cleaning_token = login('cleaning_user', 'password123')
    other_token = login('other_cleaner', 'password123')
    
    headers = {'Authorization': f'Bearer {cleaning_token}'}
    other_headers = {'Authorization': f'Bearer {other_token}'}

    # Test 1: Status transition from 'new' to 'in_progress'
    new_task = add_task(
        created_by=1,
        status='new',
        title='New Task'
    )
    
    # Test 1.1: Invalid status transition
    response = client.patch(
        f'/api/tasks/{new_task.id}',
        json={'status': 'completed'},
        headers=headers
    )
    assert response.status_code == 400
    assert "Invalid status transition" in response.json['message']
    
    # Test 1.2: Valid status transition
    response = client.patch(
        f'/api/tasks/{new_task.id}',
        json={'status': 'in_progress'},
        headers=headers
    )
    assert response.status_code == 200
    response_data = response.json
    assert "Task updated successfully" in response_data['message']
    assert 'data' in response_data
    assert 'task' in response_data['data']
    
    # Verify task was assigned to cleaning user
    updated_task = db.session.get(Task, new_task.id)
    assert updated_task.status == 'in_progress'
    assert updated_task.assigned_to == cleaning_user.id

    # Test 2: Status transitions from 'in_progress'
    # Test 2.1: Cannot modify task assigned to another user
    other_task = add_task(
        created_by=1,
        status='in_progress',
        assigned_to=other_cleaner.id,
        title='Other Task'
    )
    response = client.patch(
        f'/api/tasks/{other_task.id}',
        json={'status': 'completed'},
        headers=headers
    )
    assert response.status_code == 403
    assert "Access denied" in response.json['message']
    
    # Test 2.2: Valid transition to 'completed'
    in_progress_task1 = add_task(
        created_by=1,
        status='in_progress',
        assigned_to=cleaning_user.id,
        title='Task to Complete'
    )
    response = client.patch(
        f'/api/tasks/{in_progress_task1.id}',
        json={'status': 'completed', 'note': 'Task completed'},
        headers=headers
    )
    assert response.status_code == 200
    assert "Task updated successfully" in response.json['message']
    
    # Verify status change and log
    task = db.session.get(Task, in_progress_task1.id)
    assert task.status == 'completed'
    log = TaskLog.query.filter_by(task_id=in_progress_task1.id).order_by(TaskLog.timestamp.desc()).first()
    assert log.status == 'completed'
    assert log.note == 'Task completed'

    # Test 2.3: Valid transition to 'issue_reported'
    in_progress_task2 = add_task(
        created_by=1,
        status='in_progress',
        assigned_to=cleaning_user.id,
        title='Task with Issue'
    )
    response = client.patch(
        f'/api/tasks/{in_progress_task2.id}',
        json={'status': 'issue_reported', 'note': 'Found an issue'},
        headers=headers
    )
    assert response.status_code == 200
    assert "Task updated successfully" in response.json['message']
    
    # Verify status change and log
    task = db.session.get(Task, in_progress_task2.id)
    assert task.status == 'issue_reported'
    log = TaskLog.query.filter_by(task_id=in_progress_task2.id).order_by(TaskLog.timestamp.desc()).first()
    assert log.status == 'issue_reported'
    assert log.note == 'Found an issue'

    # Test 2.4: Valid transition to same status (in_progress)
    in_progress_task3 = add_task(
        created_by=1,
        status='in_progress',
        assigned_to=cleaning_user.id,
        title='Task Stay In Progress'
    )
    response = client.patch(
        f'/api/tasks/{in_progress_task3.id}',
        json={'status': 'in_progress', 'note': 'Still working'},
        headers=headers
    )
    assert response.status_code == 200
    assert "Task updated successfully" in response.json['message']
    
    # Verify status remains same
    task = db.session.get(Task, in_progress_task3.id)
    assert task.status == 'in_progress'
    assert task.assigned_to == cleaning_user.id

    # Test 3: Status transitions from 'issue_reported'
    issue_task = add_task(
        created_by=1,
        status='issue_reported',
        assigned_to=cleaning_user.id,
        title='Issue Task'
    )
    
    # Test 3.1: Invalid status transition
    response = client.patch(
        f'/api/tasks/{issue_task.id}',
        json={'status': 'completed'},
        headers=headers
    )
    assert response.status_code == 400
    assert "Invalid status transition" in response.json['message']
    
    # Test 3.2: Other cleaner cannot add issue details to task they're not assigned to
    response = client.patch(
        f'/api/tasks/{issue_task.id}',
        json={'status': 'issue_reported', 'note': 'Additional issue details'},
        headers=other_headers
    )
    assert response.status_code == 403
    assert "Access denied: Only the assigned user can add more issue details" in response.json['message']

    # Test 3.3: Assigned cleaner can add more issue details
    response = client.patch(
        f'/api/tasks/{issue_task.id}',
        json={'status': 'issue_reported', 'note': 'More issue details'},
        headers=headers  # Using original assigned cleaner's token
    )
    assert response.status_code == 200
    assert "Task updated successfully" in response.json['message']
    
    # Verify status and assignee remain unchanged
    task = db.session.get(Task, issue_task.id)
    assert task.status == 'issue_reported'
    assert task.assigned_to == cleaning_user.id

    # Test 3.4: Valid transition to 'in_progress' by another cleaner
    response = client.patch(
        f'/api/tasks/{issue_task.id}',
        json={'status': 'in_progress', 'note': 'Taking over the task'},
        headers=other_headers
    )
    assert response.status_code == 200
    assert "Task updated successfully" in response.json['message']
    
    # Verify task was assigned to the new cleaning user
    updated_task = db.session.get(Task, issue_task.id)
    assert updated_task.status == 'in_progress'
    assert updated_task.assigned_to == other_cleaner.id

def test_update_task_admin(client, add_user, add_task, login):
    """Test the update_task route for an 'admin' role."""
    # Add test users
    admin_user = add_user('admin_user', 'password123', 'admin')
    cleaning_user = add_user('cleaning_user', 'password123', 'cleaning_team')
    
    # Login as admin
    admin_token = login('admin_user', 'password123')
    headers = {'Authorization': f'Bearer {admin_token}'}

    # Test 1: Create test task
    task = add_task(
        created_by=admin_user.id,
        status='new',
        title='Admin Test Task'
    )

    # Test 2: Missing required fields
    response = client.patch(
        f'/api/tasks/{task.id}',
        json={'status': 'in_progress'},  # Missing assigned_to
        headers=headers
    )
    assert response.status_code == 400
    assert "Admins must provide 'status' and 'assigned_to' fields" in response.json['message']

    response = client.patch(
        f'/api/tasks/{task.id}',
        json={'assigned_to': cleaning_user.id},  # Missing status
        headers=headers
    )
    assert response.status_code == 400
    assert "Admins must provide 'status' and 'assigned_to' fields" in response.json['message']

    # Test 3: Successful task update
    response = client.patch(
        f'/api/tasks/{task.id}',
        json={
            'status': 'in_progress',
            'assigned_to': cleaning_user.id,
            'note': 'Admin assigned task'
        },
        headers=headers
    )
    assert response.status_code == 200
    response_data = response.json
    assert "Task updated successfully" in response_data['message']
    assert 'data' in response_data
    assert 'task' in response_data['data']
    
    # Verify task update in database
    updated_task = db.session.get(Task, task.id)
    assert updated_task.status == 'in_progress'
    assert updated_task.assigned_to == cleaning_user.id
    
    # Verify task log
    log = TaskLog.query.filter_by(task_id=task.id).order_by(TaskLog.timestamp.desc()).first()
    assert log.status == 'in_progress'
    assert log.assigned_to == cleaning_user.id
    assert log.modified_by == admin_user.id
    assert log.note == 'Admin assigned task'

    # Test 4: Update completed task
    completed_task = add_task(
        created_by=admin_user.id,
        status='completed',
        title='Completed Task'
    )
    response = client.patch(
        f'/api/tasks/{completed_task.id}',
        json={
            'status': 'in_progress',
            'assigned_to': cleaning_user.id
        },
        headers=headers
    )
    assert response.status_code == 403
    assert "Cannot modify completed tasks" in response.json['message']

    # Test 5: Non-existent task
    response = client.patch(
        '/api/tasks/9999',
        json={
            'status': 'in_progress',
            'assigned_to': cleaning_user.id
        },
        headers=headers
    )
    assert response.status_code == 404
    assert "Task not found" in response.json['message']
    assert "Task with ID 9999 does not exist" in response.json['error']
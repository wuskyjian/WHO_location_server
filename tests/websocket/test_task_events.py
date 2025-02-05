import pytest
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@pytest.mark.order(0)
def test_task_notification_events(app, add_user, login, create_socket_client, create_task, update_task):
    """Test WebSocket notification events for task operations."""
    print("\n=== Starting Task Notification Test ===")
    clients = []
    try:
        # Add test users
        print("\n1. Creating test users...")
        ambulance_user = add_user('ambulance_user', 'password123', 'ambulance')
        admin_user = add_user('admin_user', 'password123', 'admin')
        print(f"Created users: ambulance_user(id={ambulance_user.id}), admin_user(id={admin_user.id})")

        # Log in users
        print("\n2. Logging in users...")
        ambulance_token = login('ambulance_user', 'password123')
        admin_token = login('admin_user', 'password123')
        print("Users logged in successfully")

        # Initialize WebSocket clients
        print("\n3. Initializing WebSocket connections...")
        ambulance_client = create_socket_client(ambulance_token)
        admin_client = create_socket_client(admin_token)
        clients = [ambulance_client, admin_client]
        print("WebSocket clients connected")

        # Clear previous events
        for client in clients:
            client.get_received('/')
        print("Cleared previous events")

        # Test Case 1: Admin creates task for ambulance
        print("\n4. Testing admin creating task for ambulance...")
        task_data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'location': {'latitude': 40.7128, 'longitude': -74.0060},
            'assigned_to': ambulance_user.id
        }
        task_id = create_task(admin_token, task_data)
        print(f"Task created with ID: {task_id}")

        # Verify ambulance received notification
        ambulance_events = ambulance_client.get_received('/')
        assert len(ambulance_events) > 0, "Ambulance should receive notification for new task"
        new_task_event = next((e for e in ambulance_events if e['name'] == 'task_notification'), None)
        assert new_task_event is not None
        assert "created by admin" in new_task_event['args'][0]['message']

        # Test Case 2: Ambulance updates task with note
        print("\n5. Testing ambulance updating task with note...")
        update_data = {'note': 'Test note from ambulance'}
        update_task(ambulance_token, task_id, update_data)

        # Test Case 3: Admin updates task status
        print("\n6. Testing admin updating task status...")
        update_data = {
            'status': 'in_progress',
            'assigned_to': ambulance_user.id,
            'note': 'Status update note'
        }
        update_task(admin_token, task_id, update_data)

        # Verify ambulance received update notification
        ambulance_events = ambulance_client.get_received('/')
        status_update_event = next((e for e in ambulance_events if e['name'] == 'task_notification'), None)
        assert status_update_event is not None
        assert "Status changed" in status_update_event['args'][0]['message']

        # Test Case 4: Empty note should not trigger notification
        print("\n7. Testing update with empty note...")
        update_data = {'note': '   '}  # Empty note with spaces
        update_task(ambulance_token, task_id, update_data)
        
        # Verify no notification was sent
        events = ambulance_client.get_received('/')
        note_events = [e for e in events if e['name'] == 'task_notification' 
                      and 'Note updated' in e['args'][0]['message']]
        assert len(note_events) == 0, "Empty note should not trigger notification"

        # Test Case 5: Multiple updates
        print("\n8. Testing multiple updates...")
        updates = [
            {'note': 'First note', 'status': 'in_progress', 'assigned_to': ambulance_user.id},
            {'note': 'Second note', 'status': 'in_progress', 'assigned_to': ambulance_user.id},
            {'note': 'Completion note', 'status': 'completed', 'assigned_to': ambulance_user.id}
        ]
        
        for update in updates:
            update_task(admin_token, task_id, update)
            
        # Verify notifications
        events = ambulance_client.get_received('/')
        notifications = [e for e in events if e['name'] == 'task_notification']
        
        # Should receive notifications for non-empty notes and status changes
        assert len(notifications) > 0, "Should receive notifications for valid updates"
        
        for notification in notifications:
            message = notification['args'][0]['message']
            assert any(['Note updated' in message, 
                       'Status changed' in message]), "Notification should contain valid updates"

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise

    finally:
        # Cleanup
        print("\n9. Cleaning up...")
        for client in clients:
            if client and client.is_connected():
                client.disconnect()
        print("WebSocket clients disconnected")
        print("\n=== Task Notification Test Completed ===\n") 
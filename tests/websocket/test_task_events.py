import pytest
import logging
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@pytest.mark.order(0)
def test_task_websocket_events(app, add_user, login, create_socket_client, create_task, update_task):
    """Test WebSocket events for task operations."""
    print("\n=== Starting WebSocket Event Test ===")
    clients = []
    try:
        # Add test users
        print("\n1. Creating test users...")
        ambulance_user = add_user('ambulance_user', 'password123', 'ambulance')
        cleaning_user = add_user('cleaning_user', 'password123', 'cleaning_team')
        admin_user = add_user('admin_user', 'password123', 'admin')
        print(f"Created users: ambulance_user(id={ambulance_user.id}), "
              f"cleaning_user(id={cleaning_user.id}), admin_user(id={admin_user.id})")

        # Log in users and retrieve tokens
        print("\n2. Logging in users...")
        ambulance_token = login('ambulance_user', 'password123')
        cleaning_token = login('cleaning_user', 'password123')
        admin_token = login('admin_user', 'password123')
        print("All users logged in successfully")

        # Initialize WebSocket clients
        print("\n3. Initializing WebSocket connections...")
        ambulance_client = create_socket_client(ambulance_token)
        cleaning_client = create_socket_client(cleaning_token)
        admin_client = create_socket_client(admin_token)
        clients = [ambulance_client, cleaning_client, admin_client]
        print("All WebSocket clients connected")

        # Clear previous WebSocket events
        for client in clients:
            client.get_received('/')
        print("Cleared previous WebSocket events")

        # Create a test task
        task_data = {
            'title': 'Cleaning Task',
            'location': {
                'latitude': 40.7128,
                'longitude': -74.0060
            },
            'assigned_to': cleaning_user.id
        }
        print(f"\n4. Creating test task with data: {json.dumps(task_data, indent=2)}")

        with app.test_client() as http_client:
            # Create and update tasks
            task_id = create_task(ambulance_token, task_data)
            print(f"\nTask created with ID: {task_id}")
            
            # First update - only adding note (should not trigger WebSocket event)
            print("\n5. Adding note without status change...")
            update_data_note = {'note': 'Just adding a note'}
            update_task(ambulance_token, task_id, update_data_note)  # Ambulance user can add notes
            print("Note added to task")
            
            # Store initial events (task creation)
            initial_events = {}
            for ws_client, role in [
                (ambulance_client, 'Ambulance'),
                (cleaning_client, 'Cleaning Team'),
                (admin_client, 'Admin')
            ]:
                events = ws_client.get_received('/')
                initial_events[role] = events
                assert len(events) == 1, f"Expected 1 event for {role} (task creation), got {len(events)}"
            print("Verified no events sent for note update")
            
            # Status update - should trigger WebSocket event
            print("\n6. Updating task status to 'in_progress'...")
            update_data_cleaning = {'status': 'in_progress', 'note': 'Starting the work'}
            update_task(cleaning_token, task_id, update_data_cleaning)
            print("Task updated by cleaning team")
            
            # Another note update - should not trigger event
            print("\n7. Adding another note...")
            update_data_note2 = {
                'status': 'in_progress',
                'assigned_to': cleaning_user.id,
                'note': 'Work in progress note'
            }
            update_task(admin_token, task_id, update_data_note2)
            print("Second note added")
            
            # Final status update
            print("\n8. Updating task status to 'completed'...")
            update_data_admin = {'status': 'completed', 'assigned_to': cleaning_user.id}
            update_task(admin_token, task_id, update_data_admin)
            print("Task updated by admin")

            # Verify all events
            print("\n9. Verifying WebSocket events...")
            for ws_client, role in [
                (ambulance_client, 'Ambulance'),
                (cleaning_client, 'Cleaning Team'),
                (admin_client, 'Admin')
            ]:
                assert ws_client.is_connected(), f"{role} client is not connected"
                # Combine initial events with new events
                events = initial_events[role] + ws_client.get_received('/')
                print(f"\n{role} received {len(events)} events:")
                for i, event in enumerate(events, 1):
                    print(f"\nEvent {i}:")
                    print(f"  Name: {event['name']}")
                    print(f"  Args: {json.dumps(event['args'][0], indent=2)}")
                
                # Should receive 3 events: create, in_progress, completed
                assert len(events) == 3, f"Expected 3 events for {role}, got {len(events)}"
                
                # Verify event sequence
                statuses = [event['args'][0]['status'] for event in events]
                assert statuses == ['new', 'in_progress', 'completed'], \
                    f"Expected status sequence ['new', 'in_progress', 'completed'], got {statuses}"
                
                # Verify event structure
                for event in events:
                    assert event['name'] == 'task_updates'
                    assert 'args' in event
                    assert len(event['args']) == 1
                    task_data = event['args'][0]
                    assert all(key in task_data for key in ['id', 'status', 'title', 'db_version'])

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise

    finally:
        # Disconnect WebSocket clients
        print("\n10. Cleaning up...")
        for client in clients:
            if client and client.is_connected():
                client.disconnect()
        print("All WebSocket clients disconnected")
        print("\n=== WebSocket Event Test Completed ===\n") 
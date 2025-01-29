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
            
            # First update
            print("\n5. Updating task status to 'in_progress'...")
            update_data_cleaning = {'status': 'in_progress'}
            update_task(cleaning_token, task_id, update_data_cleaning)
            print("Task updated by cleaning team")
            
            # Second update
            print("\n6. Updating task status to 'completed'...")
            update_data_admin = {'status': 'completed', 'assigned_to': cleaning_user.id}
            update_task(admin_token, task_id, update_data_admin)
            print("Task updated by admin")

            # Verify events
            print("\n7. Verifying WebSocket events...")
            for ws_client, role in [
                (ambulance_client, 'Ambulance'),
                (cleaning_client, 'Cleaning Team'),
                (admin_client, 'Admin')
            ]:
                assert ws_client.is_connected(), f"{role} client is not connected"
                events = ws_client.get_received('/')
                print(f"\n{role} received {len(events)} events:")
                for i, event in enumerate(events, 1):
                    print(f"\nEvent {i}:")
                    print(f"  Name: {event['name']}")
                    print(f"  Args: {json.dumps(event['args'][0], indent=2)}")
                
                assert len(events) == 3, f"Expected 3 events for {role}, got {len(events)}"
                
                # Verify event structure
                for event in events:
                    assert event['name'] == 'task_updates'
                    assert 'args' in event
                    assert len(event['args']) == 1
                    task_data = event['args'][0]
                    assert 'id' in task_data
                    assert 'status' in task_data
                    assert 'title' in task_data

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise

    finally:
        # Disconnect WebSocket clients
        print("\n8. Cleaning up...")
        for client in clients:
            if client and client.is_connected():
                client.disconnect()
        print("All WebSocket clients disconnected")
        print("\n=== WebSocket Event Test Completed ===\n") 
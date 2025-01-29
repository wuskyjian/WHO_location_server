import pytest
from app import create_app, db, socketio
from app.models import User
from flask_socketio import SocketIOTestClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@pytest.fixture
def create_socket_client(app):
    """Create and connect a WebSocket client."""
    def _create_socket_client(token):
        client = SocketIOTestClient(
            app=app,
            socketio=socketio,
            namespace='/',
            auth={'token': token}
        )
        assert client.is_connected('/'), f"WebSocket client failed to connect for token: {token}"
        # logger.info(f"WebSocket client connected for token: {token}")
        return client
    return _create_socket_client

@pytest.fixture
def create_task(client):
    """Create a test task."""
    def _create_task(token, task_data):
        headers = {'Authorization': f'Bearer {token}'}
        response = client.post('/api/tasks', json=task_data, headers=headers)
        assert response.status_code == 201, "Failed to create task."
        response_data = response.json
        assert 'data' in response_data, "Response missing data field"
        task_id = response_data['data']['task_id']
        # logger.info(f"Task created successfully with ID: {task_id}")
        return task_id
    return _create_task

@pytest.fixture
def update_task(client):
    """Update a test task."""
    def _update_task(token, task_id, update_data):
        headers = {'Authorization': f'Bearer {token}'}
        response = client.patch(f'/api/tasks/{task_id}', json=update_data, headers=headers)
        assert response.status_code == 200, f"Failed to update task {task_id}."
        response_data = response.json
        assert 'data' in response_data, "Response missing data field"
        assert 'task' in response_data['data'], "Response missing task data"
        # logger.info(f"Task {task_id} updated successfully.")
        return response
    return _update_task 
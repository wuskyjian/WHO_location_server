from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token
from flask import request
from app.models import GlobalCounter

class WebSocketService:
    """Service class for WebSocket operations."""
    
    TASK_UPDATES_ROOM = 'task_updates'
    
    @classmethod
    def handle_connect(cls, auth):
        """Handle WebSocket connection and authenticate the user using a JWT token.
        
        Args:
            auth: Authentication data containing JWT token
        """
        if not auth or "token" not in auth:
            print("No token provided or auth is None")
            emit("error", {"message": "Missing or invalid token"}, to=request.sid)
            disconnect()
            return

        token = auth.get("token")
        try:
            # Decode the JWT token manually
            decoded_token = decode_token(token)
            user_identity = decoded_token['sub']  # Extract user identity from the token
            print(f"WebSocket authenticated for user: {user_identity}")
            join_room(cls.TASK_UPDATES_ROOM)  # Add the user to the task updates room
        except Exception as e:
            print(f"Token verification failed: {e}")
            emit("error", {"message": "Token verification failed"}, to=request.sid)
            disconnect()
    
    @classmethod
    def handle_disconnect(cls):
        """Handle WebSocket disconnection."""
        leave_room(cls.TASK_UPDATES_ROOM)
        print("Client disconnected")
    
    @classmethod
    def broadcast_task_update(cls, task):
        """Broadcast task update to all connected clients.
        
        Args:
            task: Task model instance
        """
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "location": {
                "latitude": task.location_lat,
                "longitude": task.location_lon
            },
            "created_by": task.created_by,
            "assigned_to": task.assigned_to,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "db_version": GlobalCounter.query.first().task_counter
        }
        
        emit('task_updates', task_data, room=cls.TASK_UPDATES_ROOM, namespace='/') 
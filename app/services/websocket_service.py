from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token
from flask import request
from app.models import GlobalCounter

class WebSocketService:
    """Service class for WebSocket operations."""
    
    TASK_UPDATES_ROOM = 'task_updates'
    user_sessions = {}  # Store user_id and request.sid mapping
    
    @classmethod
    def handle_connect(cls, auth):
        """Handle WebSocket connection and authenticate the user using a JWT token."""
        print("\n" + "=" * 50)
        print("【WebSocket Connect】")
        print(f"Auth data: {auth}")
        
        try:
            if not auth or "token" not in auth:
                raise ValueError("No token provided or auth is None")

            token = auth.get("token")
            if token.startswith("Bearer "):
                token = token[7:]
            
            # Decode the JWT token manually
            decoded_token = decode_token(token)
            user_identity = decoded_token['sub']
            
            # Join the global task updates room
            join_room(cls.TASK_UPDATES_ROOM)
            
            # Update user session
            if user_identity not in cls.user_sessions:
                cls.user_sessions[user_identity] = []
            cls.user_sessions[user_identity].append(request.sid)
            
            print(f"Authenticated user: {user_identity}")
            print(f"Joined room: {cls.TASK_UPDATES_ROOM}")
            print(f"User sessions: {cls.user_sessions}")
            print("=" * 50 + "\n")
            
            return True
            
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            print("=" * 50 + "\n")
            emit("error", {"message": str(e)}, to=request.sid)
            disconnect()
            return False
    
    @classmethod
    def handle_disconnect(cls):
        """Handle WebSocket disconnection."""
        print("\n" + "=" * 50)
        print("【WebSocket Disconnect】")
        # Remove disconnected session from user_sessions
        for user_id, sids in list(cls.user_sessions.items()):
            if request.sid in sids:
                sids.remove(request.sid)
                if not sids:  # If the list is empty, remove the entire key
                    del cls.user_sessions[user_id]
                break
        
        leave_room(cls.TASK_UPDATES_ROOM)
        print(f"Left room: {cls.TASK_UPDATES_ROOM}")
        print(f"User sessions after disconnect: {cls.user_sessions}")
        print("=" * 50 + "\n")
    
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

    @classmethod
    def broadcast_task_notification(cls, user_ids, message):
        """Broadcast a notification to specific users."""
        notify_data = {
            "notification": {
                "message": message,
                "users": user_ids
            }
        }
        emit('task_notification', notify_data, room=cls.TASK_UPDATES_ROOM, namespace='/')

    @classmethod
    def send_notification_to_users(cls, user_ids, notification_type, message):
        """Send a notification to specific users.
        
        Args:
            user_ids: List of user IDs to send the notification to
            notification_type: Type of notification (e.g. 'new_task', 'task_updated')
            message: Notification message content
        """
        print("\n" + "=" * 50)
        print("【Send Notification】")
        print(f"Target users: {user_ids}")
        print(f"Type: {notification_type}")
        print(f"Message: {message}")
        print(f"Current user_sessions: {cls.user_sessions}")
        
        # Make sure user_ids is a list of strings
        user_ids = [str(uid) for uid in user_ids]
        
        for user_id in user_ids:
            print(f"Processing user ID: {user_id} (type: {type(user_id)})")
            if user_id in cls.user_sessions:
                sessions = cls.user_sessions[user_id]
                print(f"Found {len(sessions)} active session(s) for user {user_id}")
                for sid in sessions:
                    print(f"Sending notification to SID: {sid}")
                    emit('task_notification', {
                        "message": message,
                        "type": notification_type,
                        "user_id": user_id,
                    }, to=sid, room=cls.TASK_UPDATES_ROOM, namespace='/')
            else:
                print(f"No active sessions found for user {user_id}")
        
        print("=" * 50 + "\n")
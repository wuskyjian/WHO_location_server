from flask import jsonify, current_app
from app.models import db, Task, TaskLog, User, TaskStatus
from app.utils.response import AuthError, NotFoundError
from datetime import datetime

class TaskService:
    """Service class for task-related operations."""
    
    @staticmethod
    def validate_location(location):
        """Validate location data."""
        if not isinstance(location, dict) or not all(key in location for key in ('latitude', 'longitude')):
            raise AuthError("Missing location details: latitude, longitude")
            
        try:
            lat = float(location['latitude'])
            lon = float(location['longitude'])
            Task.validate_location(lat, lon)
        except (ValueError, TypeError):
            raise AuthError("Invalid location coordinates")
        
        return lat, lon

    @staticmethod
    def create_task_log(task_id, status, modified_by, assigned_to, note=None):
        """Create a task log entry.
        
        Args:
            task_id: ID of the task
            status: Task status
            modified_by: ID of the user who modified the task
            assigned_to: ID of the user assigned to the task
            note: Optional note about the modification
        """
        log = TaskLog(
            task_id=task_id,
            status=status,
            modified_by=modified_by,
            assigned_to=assigned_to,
            note=note
        )
        db.session.add(log)
        return log

    @classmethod
    def create_task(cls, data, current_user):
        """Create a new task based on user role.
        
        Args:
            data: Request data containing task details
            current_user: Current user model instance
            
        Returns:
            Task: Created task instance
            
        Raises:
            AuthError: If validation fails or user has insufficient permissions
        """
        try:
            # Validate basic required fields
            if not isinstance(data, dict) or not all(key in data for key in ('title', 'location')):
                raise AuthError("Missing required fields: title, location")

            # Validate location
            lat, lon = cls.validate_location(data['location'])

            # Role-specific validation and assignment
            if current_user.role not in ['ambulance', 'admin']:
                raise AuthError("Access denied: Only ambulance or admin users can create tasks", 403)

            # Determine assigned_to based on role
            if current_user.role == 'admin':
                if 'assigned_to' not in data:
                    raise AuthError("Missing required field: assigned_to for admin")
                assigned_to = data['assigned_to']
                # Verify assigned user exists
                if not db.session.get(User, assigned_to):
                    raise AuthError("Invalid assigned_to user ID")
            else:  # ambulance role
                assigned_to = current_user.id

            # Create task
            task = Task(
                title=data['title'],
                created_by=current_user.id,
                location_lat=lat,
                location_lon=lon,
                description=data.get('description'),
                assigned_to=assigned_to,
                status=TaskStatus.NEW
            )
            db.session.add(task)
            db.session.flush()  # Get the task ID

            # Create task log
            log = TaskLog(
                task_id=task.id,
                status=TaskStatus.NEW,
                modified_by=current_user.id,
                assigned_to=assigned_to,
                note=f"Task created by {current_user.role} {current_user.id}"  # Match the test expectation
            )
            db.session.add(log)

            # Commit all changes
            db.session.commit()
            return task

        except Exception as e:
            db.session.rollback()
            raise e 

    @staticmethod
    def update_task(task_id, data, current_user):
        """Update task based on user role and permissions."""
        try:
            task = db.session.get(Task, task_id)
            if not task:
                raise NotFoundError(
                    message="Task not found",
                    error=f"Task with ID {task_id} does not exist"
                )

            if task.status == 'completed':
                raise AuthError("Cannot modify completed tasks", 403)
            
            note = data.get('note')
            
            # Handle different roles
            if current_user.role == 'ambulance':
                # Allow also assigned ambulance to modify task
                if task.created_by != current_user.id and task.assigned_to != current_user.id:
                    raise AuthError("Access denied: You can only modify tasks you created or are assigned to", 403)
                if not note:
                    raise ValueError("Note is required for ambulance updates")
            
            elif current_user.role == 'cleaning_team':
                new_status = data.get('status')
                if not new_status:
                    raise ValueError("Status is required for cleaning team updates")

                valid_transitions = {
                    'new': ['in_progress'],
                    'in_progress': ['completed', 'issue_reported', 'in_progress'],
                    'issue_reported': ['in_progress', 'issue_reported']
                }

                if new_status not in valid_transitions.get(task.status, []):
                    raise ValueError(
                        f"Invalid status transition from '{task.status}' to '{new_status}'. "
                        f"Valid transitions are: {valid_transitions.get(task.status, [])}"
                    )

                # Only the assigned user can modify a task when it's in progress
                if task.status == 'in_progress' and task.assigned_to != current_user.id:
                    raise AuthError("Access denied: You can only modify tasks assigned to you", 403)

                # Only the assigned user can add more issue reports
                if task.status == 'issue_reported' and new_status == 'issue_reported' and task.assigned_to != current_user.id:
                    raise AuthError("Access denied: Only the assigned user can add more issue details", 403)

                # Store original status before update
                original_status = task.status
                task.status = new_status
                # Update task assignee when task is first taken or reassigned from reported issue
                if new_status == 'in_progress' and original_status in ['new', 'issue_reported']:
                    task.assigned_to = current_user.id

            elif current_user.role == 'admin':
                if not all(key in data for key in ['status', 'assigned_to']):
                    raise ValueError("Admins must provide 'status' and 'assigned_to' fields")

                task.status = data['status']
                task.assigned_to = data['assigned_to']

            else:
                raise AuthError("Invalid role", 403)
            
            # Create task log
            task_log = TaskLog(
                task_id=task.id,
                status=task.status,
                assigned_to=task.assigned_to,
                modified_by=current_user.id,
                note=note
            )
            db.session.add(task_log)
            db.session.commit()

            return task

        except (ValueError, AuthError, NotFoundError) as e:  
            db.session.rollback()
            raise e
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating task: {str(e)}")
            raise e 
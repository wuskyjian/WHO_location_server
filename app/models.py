from app import db
from datetime import datetime
import os
import hashlib
from sqlalchemy import event, text
from enum import Enum
from config import Config

class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = 'admin'
    AMBULANCE = 'ambulance'
    CLEANING_TEAM = 'cleaning_team'

class TaskStatus(str, Enum):
    """Task status enumeration."""
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ISSUE_REPORTED = 'issue_reported'

# User model for managing user data and authentication
class User(db.Model):
    """User model for managing user data and authentication."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(Config.SERVER_TIMEZONE))
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=lambda: datetime.now(Config.SERVER_TIMEZONE))
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, username, role):
        self.username = username
        self.role = role

    def set_password(self, password):
        """Set hashed password with salt."""
        self.salt = os.urandom(16).hex()
        self.password_hash = self._hash_password(password)

    def check_password(self, password):
        """Verify password."""
        return self._hash_password(password) == self.password_hash

    def _hash_password(self, password):
        """Internal method to hash password with salt."""
        return hashlib.sha256(
            (self.salt + password).encode('utf-8')
        ).hexdigest()

    @property
    def is_admin(self):
        """Check if user is admin."""
        return self.role == UserRole.ADMIN

    @property
    def is_ambulance(self):
        """Check if user is ambulance staff."""
        return self.role == UserRole.AMBULANCE

    @property
    def is_cleaning_team(self):
        """Check if user is cleaning team member."""
        return self.role == UserRole.CLEANING_TEAM

    def to_dict(self, include_private=False):
        """Convert user to dictionary."""
        data = {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
        if include_private:
            data.update({
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            })
        return data

    def __repr__(self):
        """String representation of User."""
        return f'<User {self.username} ({self.role})>'

# Task model for managing task-related data
class Task(db.Model):
    __table_args__ = (
        db.Index('idx_task_status', 'status'),  # Index for status queries
        db.Index('idx_task_location', 'location_lat', 'location_lon'),  # Index for location queries
        db.CheckConstraint('-90 <= location_lat AND location_lat <= 90', name='check_lat'),
        db.CheckConstraint('-180 <= location_lon AND location_lon <= 180', name='check_lon'),
    )

    id = db.Column(db.Integer, primary_key=True)  # Unique task ID
    title = db.Column(db.String(255), nullable=False)  # Task title
    description = db.Column(db.Text, nullable=True)  # Task description (optional)
    status = db.Column(db.String(20), default=TaskStatus.NEW)  # Task status
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ID of the user who created the task
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # ID of the user assigned to the task
    location_lat = db.Column(db.Float, nullable=False)  # Latitude of the task location
    location_lon = db.Column(db.Float, nullable=False)  # Longitude of the task location
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(Config.SERVER_TIMEZONE))
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=lambda: datetime.now(Config.SERVER_TIMEZONE))
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tasks')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')
    logs = db.relationship('TaskLog', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    historical_assignees = db.Column(db.JSON, default=list)  # Store historical assignees as JSON array

    def to_dict(self, include_logs=False):
        """Convert task to dictionary."""
        # Get current global counter
        counter = GlobalCounter.query.first()
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'historical_assignees': self.historical_assignees,
            'location': {
                'latitude': self.location_lat,
                'longitude': self.location_lon
            },
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'global_version': counter.task_counter if counter else 0  
        }
        if include_logs:
            data['logs'] = [log.to_dict() for log in self.logs]
        return data

    @staticmethod
    def validate_location(lat, lon):
        """Validate geographic coordinates."""
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid coordinates")
        return True

    @classmethod
    def create(cls, title, created_by, location_lat, location_lon, description=None):
        """Create a new task with validation."""
        cls.validate_location(location_lat, location_lon)
        task = cls(
            title=title,
            created_by=created_by,
            location_lat=location_lat,
            location_lon=location_lon,
            description=description
        )
        db.session.add(task)
        return task

# TaskLog model for tracking changes to tasks
class TaskLog(db.Model):
    """Model for tracking task changes and maintaining audit trail."""
    
    __table_args__ = (
        db.Index('idx_tasklog_task_time', 'task_id', 'timestamp'),  # Index for efficient log retrieval
    )
    
    id = db.Column(db.Integer, primary_key=True)  # Unique log ID
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(Config.SERVER_TIMEZONE))
    status = db.Column(db.String(20), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    modified_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=False)
    note = db.Column(db.Text, nullable=True)
    
    # Add relationships for easier access
    modifier = db.relationship('User', foreign_keys=[modified_by], backref='modified_logs')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assignment_logs')

    @classmethod
    def create(cls, task_id, status, modified_by, assigned_to=None, note=None):
        """Factory method to create a new log entry."""
        log = cls(
            task_id=task_id,
            status=status,
            modified_by=modified_by,
            assigned_to=assigned_to,
            note=note
        )
        db.session.add(log)
        return log

    def to_dict(self, include_users=False):
        """Convert TaskLog to dictionary with optional user details."""
        data = {
            'id': self.id,
            'task_id': self.task_id,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'assigned_to': self.assigned_to,
            'modified_by': self.modified_by,
            'note': self.note
        }
        
        if include_users:
            data.update({
                'modifier': self.modifier.to_dict() if self.modifier else None,
                'assignee': self.assignee.to_dict() if self.assignee else None
            })
        
        return data

    def __repr__(self):
        """String representation of TaskLog."""
        return f'<TaskLog {self.id} Task:{self.task_id} Status:{self.status}>'

# GlobalCounter model for maintaining a global task counter
class GlobalCounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_counter = db.Column(db.Integer, default=0, nullable=False)  # Global task counter
    MAX_COUNTER = 2**31 - 1

    @staticmethod
    def initialize():
        """
        Initialize the global counter table to ensure at least one row exists.
        """
        if not GlobalCounter.query.first():
            counter = GlobalCounter(task_counter=0)
            db.session.add(counter)
            db.session.commit()

    @staticmethod
    def increment_counter():
        """
        Increment the global task counter with overflow check.
        """
        counter = GlobalCounter.query.first()
        if counter:
            counter.task_counter = (counter.task_counter + 1) % GlobalCounter.MAX_COUNTER
            db.session.commit()

    @staticmethod
    def reset_counter():
        """
        Reset the global task counter to zero.
        """
        counter = GlobalCounter.query.first()
        if counter:
            counter.task_counter = 0
            db.session.commit()

# Event listeners for the Task table
@event.listens_for(Task, 'after_insert')
def after_insert(mapper, connection, target):
    """
    Increment the global task counter after a new task is inserted.
    """
    connection.execute(text("UPDATE global_counter SET task_counter = (task_counter + 1) % 2147483647"))

@event.listens_for(Task, 'after_update')
def after_update(mapper, connection, target):
    """
    Increment the global task counter after a task is updated.
    Only increment when there are actual changes to the task.
    """
    if db.session.is_modified(target):
        connection.execute(text("UPDATE global_counter SET task_counter = (task_counter + 1) % 2147483647"))

@event.listens_for(Task, 'after_delete')
def after_delete(mapper, connection, target):
    """
    Increment the global task counter after a task is deleted.
    """
    connection.execute(text("UPDATE global_counter SET task_counter = (task_counter + 1) % 2147483647"))
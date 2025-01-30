# WHO Location Server

This project is a Flask-based application designed to manage and serve location-based tasks and users with real-time WebSocket updates.

## Project Structure

```
.
├── app/                    # Main application package
│   ├── __init__.py        # App initialization and factory
│   ├── models.py          # Database models
│   ├── services/          # Business logic services
│   └── migrations/        # Database migrations
├── tests/                 # Test suite
│   ├── websocket/        # WebSocket specific tests
│   └── routes/           # API route tests
├── db_tools/             # Database management tools
├── config.py             # Configuration settings
├── run.py               # Application entry point
└── requirements.txt     # Project dependencies
```

## Features

- User authentication with JWT
- Role-based access control (Admin, Ambulance, Cleaning Team)
- Real-time task updates via WebSocket
- Location-based task management
- Task status tracking and history

## Getting Started

### Prerequisites

- Python 3.8 or above
- Pip package manager

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup

1. Initialize the database:
```bash
flask db init
   flask db migrate -m "Initial migration"
flask db upgrade
```

2. Database management tools:
   - Generate test data:
     ```bash
     python db_tools/db_generate_test_data.py
     ```
   - Clear database:
     ```bash
     python db_tools/db_clear_data.py
     ```

### Running the Application

Start the server:
```bash
python run.py
```

### Testing

Run the test suite:
```bash
pytest
```

Run specific test categories:
```bash
pytest tests/websocket/  # WebSocket tests only
pytest tests/routes/     # API route tests only
```

## API Documentation

### Authentication

#### Register User
- **Endpoint**: `POST /api/auth/register`
- **Description**: Register a new user
- **Access**: Public
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string",
    "role": "string"  // "admin", "ambulance", or "cleaning_team"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "User registered successfully",
    "data": {
      "token": "string",
      "token_type": "Bearer",
      "expires_in": 3600,
      "user": {
        "id": "integer",
        "username": "string",
        "role": "string"
      }
    }
  }
  ```
- **Status Codes**:
  - `201`: User created successfully
  - `400`: Missing JSON or invalid data
  - `401`: Invalid credentials

#### Login
- **Endpoint**: `POST /api/auth/login`
- **Description**: Authenticate user and get JWT token
- **Access**: Public
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Login successful",
    "data": {
      "token": "string",
      "token_type": "Bearer",
      "expires_in": 3600,
      "user": {
        "id": "integer",
        "username": "string",
        "role": "string"
      }
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Missing JSON or missing credentials
  - `401`: Invalid username or password

#### List Users
- **Endpoint**: `GET /api/auth/users`
- **Description**: Get list of users, optionally filtered by role
- **Access**: Admin only
- **Query Parameters**:
  - `role` (optional): Filter users by role
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Retrieved {count} users",
    "data": [
      {
        "id": "integer",
        "username": "string",
        "role": "string"
      }
    ]
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `403`: Not admin

#### Delete User
- **Endpoint**: `DELETE /api/auth/users/<user_id>`
- **Description**: Delete a user by ID
- **Access**: Admin only
- **Response**:
  ```json
  {
    "status": "success",
    "message": "User {user_id} deleted successfully",
    "data": {
      "deleted_id": "integer"
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `403`: Not admin or trying to delete self
  - `404`: User not found

### Role-Based Access Control

#### User Roles
- **Admin**: Full system access
  - Can register new users
  - Can manage all tasks
  - Can access all endpoints
- **Ambulance**: Task creation and management
  - Can create new tasks
  - Can view and update assigned tasks
- **Cleaning Team**: Task execution
  - Can view and update assigned tasks
  - Can mark tasks as completed

### Task API

#### List All Tasks
- **Endpoint**: `GET /api/tasks`
- **Description**: Get a list of all tasks
- **Response**:
  ```json
  {
    "data": [
      {
        "id": "integer",
        "title": "string",
        "description": "string",
        "status": "string",
        "location": {
          "latitude": "float",
          "longitude": "float"
        },
        "created_by": "integer",
        "assigned_to": "integer",
        "created_at": "datetime",
        "updated_at": "datetime",
        "global_version": 123
      }
    ],
    "message": "Tasks retrieved successfully"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `404`: User not found

#### Get Task Details
- **Endpoint**: `GET /api/tasks/<task_id>`
- **Description**: Get detailed information about a specific task
- **Access**: All authenticated users
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Task retrieved successfully",
    "data": {
      "task": {
        "id": "integer",
        "title": "string",
        "description": "string",
        "status": "string",
        "location": {
          "latitude": "float",
          "longitude": "float"
        },
        "created_by": "integer",
        "assigned_to": "integer",
        "created_at": "datetime",
        "updated_at": "datetime",
        "logs": [
          {
            "id": "integer",
            "task_id": "integer",
            "status": "string",
            "assigned_to": "integer",
            "modified_by": "integer",
            "note": "string",
            "timestamp": "datetime"
          }
        ]
      }
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `404`: Task or user not found

#### Get Task Logs
- **Endpoint**: `GET /api/tasks/<task_id>/logs`
- **Description**: Get complete history of task updates
- **Access**: All authenticated users
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Task logs retrieved successfully",
    "data": [
      {
        "id": "integer",
        "task_id": "integer",
        "status": "string",
        "assigned_to": "integer",
        "modified_by": "integer",
        "note": "string",
        "timestamp": "datetime",
        "user": {
          "id": "integer",
          "username": "string",
          "role": "string"
        }
      }
    ]
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `404`: Task not found or no logs available

#### Create Task
- **Endpoint**: `POST /api/tasks`
- **Description**: Create a new task
- **Access**: Ambulance and Admin roles
- **Request Body**:
  ```json
  {
    "title": "string",
    "description": "string (optional)",
    "location": {
      "latitude": "float",
      "longitude": "float"
    },
    "assigned_to": "integer (required for admin)"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Task created successfully",
    "data": {
      "task_id": "integer",
      "task": {
        "id": "integer",
        "title": "string",
        "description": "string",
        "status": "string",
        "location": {
          "latitude": "float",
          "longitude": "float"
        },
        "created_by": "integer",
        "assigned_to": "integer",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    }
  }
  ```
- **Status Codes**:
  - `201`: Task created successfully
  - `400`: Invalid request data
  - `401`: Unauthorized
  - `403`: Invalid role

#### Update Task
- **Endpoint**: `PATCH /api/tasks/<task_id>`
- **Description**: Update task status, assignment, or add notes
- **Access**: Varies by role
- **Request Body**:
  ```json
  {
    "status": "string (optional)",
    "assigned_to": "integer (required for admin)",
    "note": "string (optional)"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Task updated successfully",
    "data": {
      "task": {
        "id": "integer",
        "title": "string",
        "status": "string",
        "assigned_to": "integer",
        "updated_at": "datetime"
      }
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
  - `401`: Unauthorized
  - `403`: Invalid role or permissions
  - `404`: Task not found

#### Role-Specific Update Rules
- **Ambulance**:
  - Can only modify tasks they created
  - Must provide note for updates
- **Cleaning Team**:
  - Can only modify assigned tasks
  - Must provide status change
  - Valid status transitions:
    - `new` → `in_progress`
    - `in_progress` → `completed`/`issue_reported`
    - `issue_reported` → `in_progress`
- **Admin**:
  - Can modify any task
  - Must provide status and assigned_to

#### GET /api/tasks/sync
- **Description**: Synchronize tasks with version check
- **Authentication**: Required
- **Query Parameters**:
  - `version`: Client's current version number
    - Type: integer
    - Optional: yes
    - Default: 0
    - Note: Invalid values will be treated as 0
- **Responses**:
  - `304`: No changes (when client version matches server version)
  - `200`: Changes available
    ```json
    {
      "data": {
        "version": 123,
        "needs_sync": true,
        "tasks": [
          {
            "id": 1,
            "title": "Task Title",
            "description": "Task Description",
            "status": "new",
            "created_by": 1,
            "assigned_to": 2,
            "location": {
              "latitude": 12.345678,
              "longitude": 98.765432
            },
            "created_at": "2024-03-20T10:30:00+00:00",
            "updated_at": "2024-03-20T10:30:00+00:00",
            "global_version": 123
          }
        ]
      }
    }
    ```
  - `401`: Unauthorized

### Reports API

#### Generate Report
- **Endpoint**: `GET /api/generate-report`
- **Description**: Generate a task statistics report for a specific date
- **Access**: Admin only
- **Query Parameters**:
  - `date` (optional): Target date in YYYY-MM-DD format
    - Defaults to today if not provided
    - Cannot be a future date
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Report generated successfully",
    "data": {
      "filename": "daily_task_report_2024-03-20_15-30-45.txt",
      "report": "string (report content)"
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid date format or future date
  - `401`: Unauthorized
  - `403`: Not admin

#### List Reports
- **Endpoint**: `GET /api/reports`
- **Description**: Get a list of all available report files
- **Access**: All authenticated users
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Reports retrieved successfully",
    "data": {
      "files": [
        "daily_task_report_2024-03-20_15-30-45.txt",
        "daily_task_report_2024-03-19_14-25-30.txt"
      ]
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `404`: No reports found

#### Download Report
- **Endpoint**: `GET /api/reports/<filename>`
- **Description**: Download a specific report file
- **Access**: All authenticated users
- **Parameters**:
  - `filename`: Name of the report file (e.g., "daily_task_report_2024-03-20_15-30-45.txt")
- **Response**: 
  - Content-Type: text/plain
  - File download with report content
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `404`: Report file not found

#### Report Format
```
Daily Task Statistics (2024-03-20)
----------------------------------------
Tasks Created: 5

Task Status Distribution:
  - completed: 10
  - in_progress: 8
  - issue_reported: 3

Reported Issues Details:
----------------------------------------
Task ID: 1
Title: Water Leak
Description: Major water leak in building A
Created By: john_doe
Assigned To: alice_smith
Location: (123.456, 789.012)
Task Logs:
  - [2024-03-20 10:15:20] Status: new - Created by: john_doe - Note: Task created
  - [2024-03-20 14:20:30] Status: in_progress - Assigned to: bob_worker
  - [2024-03-20 15:30:45] Status: issue_reported - Assigned to: alice_smith - Note: Found critical issue
----------------------------------------
```

### WebSocket Events

#### Connection
- **URL**: `ws://host:port/`
- **Authentication**: JWT token required in connection data
  ```json
  {
    "token": "your-jwt-token"
  }
  ```
- **Events**:
  - `connect`: Triggered on connection attempt
    - Requires authentication data
    - Automatically joins task updates room on success
  - `disconnect`: Triggered when client disconnects
    - Automatically leaves task updates room

#### Task Updates
- **Event**: `task_updates`
- **Direction**: Server → Client
- **Trigger Conditions**:
  - Task creation
  - Task status changes
  - Not triggered for note-only updates
- **Room**: All authenticated clients in 'task_updates' room
- **Payload**:
  ```json
  {
    "id": "integer",
    "title": "string",
    "description": "string",
    "status": "string",
    "location": {
      "latitude": "float",
      "longitude": "float"
    },
    "created_by": "integer",
    "assigned_to": "integer",
    "created_at": "datetime",
    "updated_at": "datetime",
    "db_version": "integer"
  }
  ```

#### Error Events
- **Event**: `error`
- **Direction**: Server → Client
- **Conditions**:
  - Missing or invalid token
  - Token verification failure
- **Payload**:
  ```json
  {
    "message": "string"  // Error description
  }
  ```

#### Event Optimization
- Events are only broadcast when task status changes
- Note-only updates do not trigger broadcasts
- All connected clients receive updates simultaneously
- Automatic room management for connected clients
- Automatic disconnection on authentication failure

### Project Components

- **Models**: User, Task, and TaskLog models in `app/models.py`
- **Services**: Business logic in `app/services/`
- **Tests**: Comprehensive test suite in `tests/`
- **Configuration**: Environment-specific settings in `config.py`

### Testing

The project includes comprehensive tests for:
- WebSocket functionality
- API endpoints
- Authentication
- Database operations

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

#### Login
- **Endpoint**: `POST /api/auth/login`
- **Description**: Authenticate user and retrieve JWT token
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string" // Password is plain text
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
  - `401`: Invalid credentials
  - `400`: Missing JSON in request

#### Register
- **Endpoint**: `POST /api/auth/register`
- **Description**: Register a new user
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string", // Password is plain text
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
  - `201`: User created
  - `400`: Missing JSON in request or validation error
  - `401`: Unauthorized

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
- **Description**: Get detailed information about a specific task, including its logs
- **Response**:
  ```json
  {
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
    },
    "message": "Task retrieved successfully"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `404`: Task or user not found

#### Get Task Logs
- **Endpoint**: `GET /api/tasks/<task_id>/logs`
- **Description**: Get the complete history of task updates and modifications
- **Response**:
  ```json
  {
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
    ],
    "message": "Task logs retrieved successfully"
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
    }
  }
  ```
- **Response**:
  ```json
  {
    "data": {
      "task_id": "integer",
      "task": {
        "id": "integer",
        "title": "string",
        "status": "new",
        "location": {
          "latitude": "float",
          "longitude": "float"
        },
        "created_by": "integer",
        "assigned_to": "integer",
        "created_at": "datetime"
      }
    }
  }
  ```
- **Status Codes**:
  - `201`: Task created
  - `401`: Unauthorized
  - `422`: Validation error

#### Update Task
- **Endpoint**: `PATCH /api/tasks/<task_id>`
- **Description**: Update task status or assignment
- **Request Body**:
  ```json
  {
    "status": "string (optional)",
    "assigned_to": "integer (optional)"
  }
  ```
- **Response**:
  ```json
  {
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
  - `404`: Task not found
  - `401`: Unauthorized
  - `422`: Validation error

#### Task Status Flow
- `new` → `in_progress` → `completed`
- Only assigned cleaning team can mark task as `in_progress`
- Admin can change any task status

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
- **Description**: Generate a new report
- **Access**: Admin only
- **Response**:
  ```json
  {
    "data": {
      "filename": "string",
      "report": "string"
    },
    "message": "Report generated successfully"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `403`: Not admin

#### List Reports
- **Endpoint**: `GET /api/reports`
- **Description**: Get a list of all available reports
- **Response**:
  ```json
  {
    "data": {
      "files": [
        "string"
      ]
    },
    "message": "Reports retrieved successfully"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `404`: No reports found

#### Download Report
- **Endpoint**: `GET /api/reports/<filename>`
- **Description**: Download a specific report file
- **Parameters**:
  - `filename`: Name of the report file to download
- **Response**: File download
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `404`: Report not found

### WebSocket Events
- `task_updates`: Real-time task status updates
- `location_updates`: Real-time location updates

## Development

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

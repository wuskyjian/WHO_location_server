from flask import Blueprint, send_file, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Task, TaskLog, User, GlobalCounter
from app import socketio
from app.services.report_service import ReportService
from app.services.websocket_service import WebSocketService
from app.services.task_service import TaskService
from app.utils.decorators import handle_api_error, admin_required
from app.utils.response import success_response, error_response, redirect_response, AuthError, NotFoundError
import os
from datetime import datetime, date

bp = Blueprint('api', __name__)

# ----------------------
# WebSocket Routes
# ----------------------

@socketio.on('connect')
def handle_connect(auth):
    """Handle WebSocket connection."""
    WebSocketService.handle_connect(auth)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    WebSocketService.handle_disconnect()

# ----------------------
# Task Routes
# ----------------------

@bp.route('/tasks', methods=['POST'])
@jwt_required()
def add_task():
    """Create new task endpoint."""
    try:
        current_user = db.session.get(User, get_jwt_identity())
        if not current_user:
            return error_response("User not found", status_code=404)

        task = TaskService.create_task(request.json, current_user)
        WebSocketService.broadcast_task_update(task)
        
        return success_response(
            data={
                "task_id": task.id,
                "task": task.to_dict()
            },
            message="Task created successfully",
            status_code=201
        )
        
    except AuthError as e:
        return error_response(message=e.message, status_code=e.status_code)
    except Exception as e:
        current_app.logger.error(f"Error creating task: {str(e)}")
        return error_response(
            message="Internal server error",
            error=str(e) if current_app.debug else None,
            status_code=500
        )

@bp.route('/tasks/<int:task_id>', methods=['PATCH'])
@jwt_required()
def update_task(task_id):
    """Update task endpoint."""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = db.session.get(User, current_user_id)
        if not current_user:
            return error_response("User not found", status_code=404)

        task = TaskService.update_task(task_id, request.json, current_user)
        WebSocketService.broadcast_task_update(task)

        return success_response(
            data={"task": task.to_dict()},
            message="Task updated successfully"
        )

    except ValueError as e:
        return error_response(message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            message=e.message,
            error=e.error if hasattr(e, 'error') else None,
            status_code=e.status_code
        )
    except AuthError as e:
        return error_response(message=e.message, status_code=e.status_code)
    except Exception as e:
        current_app.logger.error(f"Error updating task: {str(e)}")
        return error_response(
            message="Internal server error",
            error=str(e) if current_app.debug else None,
            status_code=500
        )

@bp.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
@handle_api_error
def get_task(task_id):
    """Get single task details endpoint."""
    current_user = db.session.get(User, int(get_jwt_identity()))
    if not current_user:
        return error_response("User not found", status_code=404)

    task = db.session.get(Task, task_id)
    if not task:
        return error_response(
            message="Task not found",
            error=f"Task with ID {task_id} does not exist",
            status_code=404
        )

    task_data = task.to_dict()
    task_data['logs'] = [log.to_dict() for log in task.logs.order_by(TaskLog.timestamp.desc()).all()]

    return success_response(
        data={"task": task_data},
        message="Task retrieved successfully"
    )

@bp.route('/tasks/<int:task_id>/logs', methods=['GET'])
@jwt_required()
@handle_api_error
def get_task_logs(task_id):
    """Get task logs endpoint."""
    task = db.session.get(Task, task_id)
    if not task:
        return error_response(f"Task with ID {task_id} not found", status_code=404)

    logs = task.logs.order_by(TaskLog.timestamp.desc()).all()
    if not logs:
        return error_response(f"No logs found for task ID {task_id}", status_code=404)

    return success_response(
        data=[log.to_dict(include_users=True) for log in logs],
        message="Task logs retrieved successfully"
    )

@bp.route('/tasks', methods=['GET'])
@jwt_required()
@handle_api_error
def get_all_tasks():
    """Get all tasks endpoint."""
    current_user = db.session.get(User, int(get_jwt_identity()))
    if not current_user:
        return error_response("User not found", status_code=404)
        
    tasks = Task.query.all()
    return success_response(
        data=[task.to_dict() for task in tasks],
        message="Tasks retrieved successfully"
    )

@bp.route('/tasks/sync', methods=['GET'])
@jwt_required()
@handle_api_error
def sync_tasks():
    """Sync tasks with version check."""
    client_version = request.args.get('version', type=int, default=0)
    current_version = GlobalCounter.query.first().task_counter
    
    if client_version == current_version:
        return redirect_response(status_code=304)
    
    tasks = Task.query.all()
    return success_response(
        data={
            "version": current_version,
            "needs_sync": True,
            "tasks": [task.to_dict() for task in tasks]
        }
    )

# ----------------------
# Report Routes
# ----------------------

@bp.route("/generate-report", methods=["GET"])
@jwt_required()
@admin_required
@handle_api_error
def generate_report():
    """Generate report endpoint with optional date parameter."""
    date_str = request.args.get('date')
    today = date.today()
    
    if date_str:
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Check if date is in the future
            if report_date > today:
                return error_response("Cannot generate report for future dates", 400)
        except ValueError:
            return error_response("Invalid date format. Please use YYYY-MM-DD format.", 400)
    else:
        report_date = today
        
    filename, report_text = ReportService.generate_report(report_date=report_date)
    return success_response(
        data={
            "filename": filename,
            "report": report_text
        },
        message="Report generated successfully"
    )

@bp.route("/reports", methods=["GET"])
@jwt_required()
@handle_api_error
def list_reports():
    """List reports endpoint."""
    files = ReportService.list_reports()
    if not files:
        return error_response("No reports found", status_code=404)
        
    return success_response(
        data={"files": files},
        message="Reports retrieved successfully"
    )

@bp.route("/reports/<string:filename>", methods=["GET"])
@jwt_required()
@handle_api_error
def get_report(filename):
    """Download report endpoint."""
    file_path = ReportService.get_report_file(filename)
    return send_file(file_path, as_attachment=True)

from flask import Blueprint, send_file, request, current_app, jsonify
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
        
        # Only send notification if admin creates task for ambulance
        if current_user.role == 'admin' and task.assigned_to != current_user.id:
            WebSocketService.send_notification_to_users(
                [task.assigned_to],
                "new_task",
                f"You have a new assigned task created by admin {current_user.username}. Task ID: {task.id}, Title: {task.title}, Description: {task.description}"
            )
        
        return success_response(
            data={
                "task_id": task.id,
                "task": task.to_dict()
            },
            message="Task created successfully",
            status_code=201
        )
        
    except ValueError as e:
        return error_response(message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error=getattr(e, 'error', None)
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
    try:
        current_user_id = int(get_jwt_identity())
        current_user = db.session.get(User, current_user_id)
        if not current_user:
            return error_response("User not found", status_code=404)

        old_task = db.session.get(Task, task_id)
        if not old_task:
            return error_response("Task not found", status_code=404)
        old_status = old_task.status
        old_assigned = old_task.assigned_to

        task = TaskService.update_task(task_id, request.json, current_user)
        
        changes = []
        # Check if status has changed  
        if 'status' in request.json and task.status != old_status:
            changes.append(f"Status changed from '{old_status}' to '{task.status}'")
        # Check if assigned_to has changed
        if 'assigned_to' in request.json and task.assigned_to != old_assigned:
            changes.append(f"Assigned changed from '{old_assigned}' to '{task.assigned_to}'")
        # Check if note has changed
        if 'note' in request.json and request.json['note'].strip():  
            changes.append(f"Note updated: {request.json['note']}")
        
        if changes:
            updater_name = getattr(current_user, 'username', None) or str(current_user_id)
            message = f"Task '{task.title}' updated by {updater_name}: " + "; ".join(changes)
            
            # Get all assigned users from TaskLog except current user
            task_logs = TaskLog.query.filter_by(task_id=task_id).all()
            involved_users = set(log.assigned_to for log in task_logs 
                              if log.assigned_to is not None and log.assigned_to != current_user_id)
            
            # Send notification if there are recipients
            if involved_users:
                WebSocketService.send_notification_to_users(
                    list(involved_users),
                    "task_updated",
                    message
                )

        return success_response(
            data={"task": task.to_dict()},
            message="Task updated successfully"
        )

    except ValueError as e:
        return error_response(message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error=getattr(e, 'error', None)
        )
    except AuthError as e:
        return error_response(message=e.message, status_code=e.status_code)
    except Exception as e:
        current_app.logger.error(f"Error updating task: {str(e)}")
        return error_response(
            message="Internal server error",
            status_code=500,
            error=str(e) if current_app.debug else None
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

@bp.route("/reports/<string:filename>", methods=["DELETE"])
@jwt_required()
@admin_required
@handle_api_error
def delete_report(filename):
    """Delete report endpoint."""
    try:
        ReportService.delete_report(filename)
        return jsonify({'message': f'Report {filename} deleted successfully'}), 200
    except AuthError as e:
        return jsonify({'error': str(e)}), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500
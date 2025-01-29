from datetime import datetime, timedelta
from app import db
from app.models import Task, TaskLog, User
import pytz
import os
from flask import current_app
from app.utils.response import AuthError
from config import Config

class ReportService:
    """Service class for report-related operations."""
    
    @staticmethod
    def get_task_statistics():
        """Get task statistics for the current day."""
        # Define timezone and get current time
        local_tz = Config.SERVER_TIMEZONE  # Use configured timezone
        utc_tz = pytz.utc
        local_now = datetime.now(local_tz)

        # Calculate start and end of the day in local time, then convert to UTC
        local_start_of_day = local_tz.localize(datetime.combine(local_now.date(), datetime.min.time()))
        local_end_of_day = local_start_of_day + timedelta(days=1)
        start_of_day_utc = local_start_of_day.astimezone(utc_tz)
        end_of_day_utc = local_end_of_day.astimezone(utc_tz)

        # Query task statistics
        tasks_created_today = Task.query.filter(Task.created_at.between(start_of_day_utc, end_of_day_utc)).count()
        tasks_completed_today = TaskLog.query.filter(
            TaskLog.timestamp.between(start_of_day_utc, end_of_day_utc),
            TaskLog.status == 'completed'
        ).count()
        tasks_reported_today = TaskLog.query.filter(
            TaskLog.timestamp.between(start_of_day_utc, end_of_day_utc),
            TaskLog.status == 'issue_reported'
        ).count()

        # Query task status distribution
        task_status_distribution = dict(db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status).all())

        # Subquery to get the latest TaskLog for each Task
        latest_tasklog_subquery = db.session.query(
            TaskLog.task_id,
            db.func.max(TaskLog.timestamp).label('latest_timestamp')
        ).group_by(TaskLog.task_id).subquery()

        # Query tasks with status 'issue_reported' and their latest TaskLog note
        reported_issues = db.session.query(
            Task.id,
            Task.title,
            Task.description,
            Task.created_by,
            Task.assigned_to,
            Task.location_lat,
            Task.location_lon,
            TaskLog.note
        ).join(TaskLog, Task.id == TaskLog.task_id) \
         .join(latest_tasklog_subquery, db.and_(
             TaskLog.task_id == latest_tasklog_subquery.c.task_id,
             TaskLog.timestamp == latest_tasklog_subquery.c.latest_timestamp
         )) \
         .filter(Task.status == 'issue_reported') \
         .all()

        return {
            'tasks_created_today': tasks_created_today,
            'tasks_completed_today': tasks_completed_today,
            'tasks_reported_today': tasks_reported_today,
            'task_status_distribution': task_status_distribution,
            'reported_issues': reported_issues
        }

    @staticmethod
    def format_statistics_report(statistics):
        """Format the report text."""
        report = [
            f"Daily Task Statistics ({datetime.now().date()})",
            "-" * 40,
            f"Tasks Created Today: {statistics['tasks_created_today']}",
            f"Tasks Completed Today: {statistics['tasks_completed_today']}",
            f"Tasks Reported Issues Today: {statistics['tasks_reported_today']}",
            "",
            "Task Status Distribution:",
            *[f"  - {status}: {count}" for status, count in statistics['task_status_distribution'].items()],
            "",
            "Reported Issues Details:"
        ]

        # Handle empty reported issues
        if not statistics['reported_issues']:
            report.append("  No issues reported")
        else:
            report.extend([
                f"  - Task ID: {issue[0]}\n"
                f"    Title: {issue[1]}\n"
                f"    Description: {issue[2]}\n"
                f"    Created By: {issue[3]}\n"
                f"    Assigned To: {issue[4]}\n"
                f"    Location: ({issue[5]}, {issue[6]})\n"
                f"    Latest Note: {issue[7]}"
                for issue in statistics['reported_issues']
            ])

        return "\n".join(report)

    @classmethod
    def generate_report(cls, statistics=None):
        """Generate a report file from task statistics."""
        try:
            # Get statistics if not provided
            if statistics is None:
                statistics = cls.get_task_statistics()
                
            # Format the report
            report_text = cls.format_statistics_report(statistics)
            
            # Generate filename
            current_time = datetime.now()
            filename = f"daily_task_report_{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            
            # Get and validate reports directory
            reports_dir = cls.get_reports_dir()
            
            # Write report to file
            file_path = os.path.join(reports_dir, filename)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("-" * 40 + "\n")
                file.write(report_text)
                
            return filename, report_text
            
        except Exception as e:
            current_app.logger.error(f"Error generating report: {str(e)}")
            raise AuthError(f"Failed to generate report: {str(e)}")

    @staticmethod
    def get_reports_dir():
        """Get and ensure reports directory exists.
        
        Returns:
            str: Path to reports directory
            
        Raises:
            AuthError: If directory cannot be created or accessed
        """
        reports_dir = current_app.config.get('REPORTS_DIR', 'reports')
        try:
            os.makedirs(reports_dir, exist_ok=True)
            return reports_dir
        except Exception as e:
            raise AuthError(f"Cannot access reports directory: {str(e)}")

    @classmethod
    def list_reports(cls):
        """List all available reports with metadata.
        
        Returns:
            list: List of report file information
            
        Raises:
            AuthError: If reports directory cannot be accessed
        """
        reports_dir = cls.get_reports_dir()
        
        try:
            files = []
            for filename in os.listdir(reports_dir):
                file_path = os.path.join(reports_dir, filename)
                if os.path.isfile(file_path):
                    files.append({
                        "name": filename,
                        "size": os.path.getsize(file_path),
                        "modified_time": datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    })
            return files
            
        except Exception as e:
            raise AuthError(f"Error listing reports: {str(e)}")

    @classmethod
    def get_report_file(cls, filename):
        """Get a specific report file path.
        
        Args:
            filename: Name of the report file
            
        Returns:
            str: Full path to the report file
            
        Raises:
            AuthError: If file doesn't exist or cannot be accessed
        """
        reports_dir = cls.get_reports_dir()
        file_path = os.path.join(reports_dir, filename)
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise AuthError(f"Report file '{filename}' not found", status_code=404)
            
        return file_path
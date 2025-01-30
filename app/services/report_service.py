from datetime import datetime, timedelta, date
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
    def get_task_statistics(target_date=None):
        """Get task statistics for the specified date.
        
        Args:
            target_date (date, optional): The date to get statistics for. Defaults to today.
        """
        # Define timezone and get target date
        local_tz = Config.SERVER_TIMEZONE
        utc_tz = pytz.utc
        
        if target_date is None:
            target_date = datetime.now(local_tz).date()
            
        # Calculate start and end of the target date in local time, then convert to UTC
        local_start_of_day = local_tz.localize(datetime.combine(target_date, datetime.min.time()))
        local_end_of_day = local_start_of_day + timedelta(days=1)
        start_of_day_utc = local_start_of_day.astimezone(utc_tz)
        end_of_day_utc = local_end_of_day.astimezone(utc_tz)

        # Query task statistics
        tasks_created_today = Task.query.filter(Task.created_at.between(start_of_day_utc, end_of_day_utc)).count()

        # Query task status distribution for tasks that exist on the target date
        task_status_distribution = dict(
            db.session.query(Task.status, db.func.count(Task.id))
            .filter(Task.created_at <= end_of_day_utc)  # Tasks that were created on or before the end of target date
            .group_by(Task.status)
            .all()
        )

        # Query tasks with status 'issue_reported' that exist on the target date
        reported_tasks = db.session.query(
            Task.id,
            Task.title,
            Task.description,
            Task.created_by,
            Task.assigned_to,
            Task.location_lat,
            Task.location_lon
        ).filter(
            Task.status == 'issue_reported',
            Task.created_at <= end_of_day_utc
        ).all()

        # Get logs for each task
        reported_issues = []
        for task in reported_tasks:
            task_logs = TaskLog.query.filter(
                TaskLog.task_id == task[0]  # task[0] is Task.id
            ).order_by(TaskLog.timestamp.asc()).all()
            
            # Get user names for the task
            task_creator = db.session.get(User, task[3]) if task[3] is not None else None
            task_assignee = db.session.get(User, task[4]) if task[4] is not None else None
            
            # Convert task tuple to list and append logs
            task_data = list(task)
            task_data[3] = task_creator.username if task_creator else "Unknown"
            task_data[4] = task_assignee.username if task_assignee else "Unassigned"
            
            # Get logs with user names
            task_data.append([
                {
                    'note': log.note,
                    'status': log.status,
                    'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'assigned_to': (task_creator.username if task_creator else "Unknown") 
                        if log.status == 'new' 
                        else (db.session.get(User, log.assigned_to).username if log.assigned_to is not None else "Unassigned")
                } for log in task_logs
            ])
            reported_issues.append(task_data)

        return {
            'tasks_created_today': tasks_created_today,
            'task_status_distribution': task_status_distribution,
            'reported_issues': reported_issues
        }

    @staticmethod
    def format_statistics_report(statistics, report_date=None):
        """Format the report text.
        
        Args:
            statistics (dict): The statistics to format
            report_date (date, optional): The date of the report. Defaults to today.
        """
        if report_date is None:
            report_date = date.today()
            
        report = [
            f"Daily Task Statistics ({report_date})",
            "-" * 40,
            f"Tasks Created: {statistics['tasks_created_today']}",
            "",
            "Task Status Distribution:",
            *[f"  - {status}: {count}" for status, count in statistics['task_status_distribution'].items()],
            "",
            "Reported Issues Details:",
            "-" * 40  # Add separator before issues
        ]

        # Handle empty reported issues
        if not statistics['reported_issues']:
            report.append("  No issues reported")
        else:
            for issue in statistics['reported_issues']:
                report.extend([
                    f"Task ID: {issue[0]}",
                    f"Title: {issue[1]}",
                    f"Description: {issue[2]}",
                    f"Created By: {issue[3]}",
                    f"Assigned To: {issue[4]}",
                    f"Location: ({issue[5]}, {issue[6]})",
                    "Task Logs:"
                ])
                # Add all logs for this task
                for log in issue[7]:
                    log_line = f"  - [{log['timestamp']}] Status: {log['status']}"
                    if log['assigned_to']:
                        prefix = "Created by" if log['status'] == 'new' else "Assigned to"
                        log_line += f" - {prefix}: {log['assigned_to']}"
                    if log['note']:
                        log_line += f" - Note: {log['note']}"
                    report.append(log_line)
                report.append("-" * 40)  # Add separator between tasks

        return "\n".join(report)

    @classmethod
    def generate_report(cls, report_date=None):
        """Generate a report file from task statistics for specified date.
        
        Args:
            report_date (date, optional): The date to generate report for. Defaults to today.
            
        Returns:
            tuple: (filename, report_text)
            
        Raises:
            AuthError: If report generation fails
        """
        try:
            # Get statistics for the specified date
            statistics = cls.get_task_statistics(report_date)
                
            # Format the report
            report_text = cls.format_statistics_report(statistics, report_date)
            
            # Generate filename with current timestamp
            current_time = datetime.now()
            filename = f"daily_task_report_{report_date.strftime('%Y-%m-%d')}_{current_time.strftime('%H-%M-%S')}.txt"
            
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
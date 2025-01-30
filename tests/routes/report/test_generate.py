from app import db
from app.models import Task
import os
from datetime import datetime, date, timedelta

def test_generate_report(client, add_user, login, tmp_path):
    """Test report generation functionality."""
    try:
        # Setup test users with different roles
        admin_user = add_user('report_admin', 'password123', 'admin')
        normal_user = add_user('normal_user', 'password123', 'ambulance')
        
        admin_token = login('report_admin', 'password123')
        normal_token = login('normal_user', 'password123')

        # Set up reports directory
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        client.application.config['REPORTS_DIR'] = str(reports_dir)

        # Create test tasks with different statuses
        tasks = [
            Task(title="Task 1", status="completed", created_by=admin_user.id, location_lat=0.0, location_lon=0.0),
            Task(title="Task 2", status="in_progress", created_by=normal_user.id, location_lat=1.0, location_lon=1.0),
            Task(title="Task 3", status="issue_reported", created_by=admin_user.id, location_lat=2.0, location_lon=2.0)
        ]
        db.session.add_all(tasks)
        db.session.commit()

        # Test access control
        response = client.get('/api/generate-report', headers={'Authorization': f'Bearer {normal_token}'})
        assert response.status_code == 403

        # Test successful report generation for today
        response = client.get('/api/generate-report', headers={'Authorization': f'Bearer {admin_token}'})
        assert response.status_code == 200
        assert "Report generated successfully" in response.json['message']
        assert 'filename' in response.json['data']
        assert 'report' in response.json['data']
        
        # Check filename format
        filename = response.json['data']['filename']
        assert filename.startswith(f"daily_task_report_{date.today().strftime('%Y-%m-%d')}_")
        assert filename.endswith(".txt")
        assert len(filename.split("_")[-1]) == 12  # "HH-MM-SS.txt" is 12 characters

        # Test report generation for a specific date
        yesterday = date.today() - timedelta(days=1)
        response = client.get(
            f'/api/generate-report?date={yesterday.strftime("%Y-%m-%d")}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        filename = response.json['data']['filename']
        assert filename.startswith(f"daily_task_report_{yesterday.strftime('%Y-%m-%d')}_")
        assert filename.endswith(".txt")

        # Test report generation for future date
        tomorrow = date.today() + timedelta(days=1)
        response = client.get(
            f'/api/generate-report?date={tomorrow.strftime("%Y-%m-%d")}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 400
        assert "Cannot generate report for future dates" in response.json['message']

        # Test invalid date format
        response = client.get(
            '/api/generate-report?date=2024/03/20',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 400
        assert "Invalid date format" in response.json['message']

        # Verify files were created
        report_files = os.listdir(reports_dir)
        assert len(report_files) == 2  # One for today and one for yesterday
        
        # Verify report content for today's report
        today_report = next(f for f in report_files if date.today().strftime('%Y-%m-%d') in f)
        with open(reports_dir / today_report, 'r') as f:
            content = f.read()
            assert "Task Statistics" in content
            assert "completed: 1" in content
            assert "in_progress: 1" in content
            assert "issue_reported: 1" in content

    finally:
        # Clean up test files
        if reports_dir.exists():
            for file in reports_dir.iterdir():
                file.unlink()
            reports_dir.rmdir() 
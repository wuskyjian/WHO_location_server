from app import db
from app.models import Task
import os

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

        # Test successful report generation
        response = client.get('/api/generate-report', headers={'Authorization': f'Bearer {admin_token}'})
        assert response.status_code == 200
        assert "Report generated successfully" in response.json['message']
        assert 'filename' in response.json['data']
        assert 'report' in response.json['data']

        # Verify file was created
        assert len(os.listdir(reports_dir)) == 1
        report_file = os.listdir(reports_dir)[0]
        
        # Verify report content
        with open(reports_dir / report_file, 'r') as f:
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
def test_download_report(client, add_user, login, tmp_path):
    """Test report download functionality."""
    try:
        # Setup test users
        admin_user = add_user('download_admin', 'password123', 'admin')
        normal_user = add_user('normal_user', 'password123', 'ambulance')
        
        admin_token = login('download_admin', 'password123')
        normal_token = login('normal_user', 'password123')

        # Set up reports directory and test file
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        client.application.config['REPORTS_DIR'] = str(reports_dir)

        test_content = "Test report content"
        test_file = reports_dir / "test_report.txt"
        with open(test_file, 'w') as f:
            f.write(test_content)

        # Test non-existent file
        response = client.get('/api/reports/nonexistent.txt', 
                            headers={'Authorization': f'Bearer {normal_token}'})
        assert response.status_code == 404
        response_data = response.get_json()
        assert 'message' in response_data
        assert f"Report file 'nonexistent.txt' not found" == response_data['message']

        # Test successful download
        response = client.get('/api/reports/test_report.txt', 
                            headers={'Authorization': f'Bearer {normal_token}'})
        assert response.status_code == 200
        assert response.headers['Content-Disposition'] == 'attachment; filename=test_report.txt'
        assert test_content.encode('utf-8') in response.data

    finally:
        # Clean up test files
        if reports_dir.exists():
            for file in reports_dir.iterdir():
                file.unlink()
            reports_dir.rmdir() 
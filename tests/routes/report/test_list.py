def test_list_reports(client, add_user, login, tmp_path):
    """Test listing available reports."""
    try:
        # Setup test users
        admin_user = add_user('list_admin', 'password123', 'admin')
        normal_user = add_user('normal_user', 'password123', 'ambulance')
        
        admin_token = login('list_admin', 'password123')
        normal_token = login('normal_user', 'password123')

        # Set up reports directory
        reports_dir = tmp_path / "reports"
        client.application.config['REPORTS_DIR'] = str(reports_dir)

        # Test with non-existent directory
        response = client.get('/api/reports', headers={'Authorization': f'Bearer {admin_token}'})
        assert response.status_code == 404
        assert "No reports found" in response.json['message']

        # Create directory and test files
        reports_dir.mkdir(exist_ok=True)
        test_files = ["report1.txt", "report2.txt"]
        for filename in test_files:
            (reports_dir / filename).touch()

        # Test successful listing
        response = client.get('/api/reports', headers={'Authorization': f'Bearer {normal_token}'})
        assert response.status_code == 200
        response_data = response.json
        assert 'data' in response_data
        assert 'files' in response_data['data']
        files = response_data['data']['files']
        assert len(files) == 2
        
        # Verify file metadata
        for file_info in files:
            assert all(key in file_info for key in ['name', 'size', 'modified_time'])
            assert file_info['name'] in test_files

    finally:
        # Clean up test files
        if reports_dir.exists():
            for file in reports_dir.iterdir():
                file.unlink()
            reports_dir.rmdir() 
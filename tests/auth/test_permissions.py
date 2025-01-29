
def test_protected_routes(client, add_user):
    """Test JWT protected routes."""
    # Add test user and get token
    add_user('testuser', 'password123', 'ambulance')
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    token = response.get_json()['data']['token']

    # Test accessing protected route with valid token
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/api/tasks', headers=headers)
    assert response.status_code == 200
    response_data = response.get_json()
    assert 'message' in response_data
    assert 'data' in response_data

    # Test accessing protected route without token
    response = client.get('/api/tasks')
    assert response.status_code == 401
    assert 'msg' in response.get_json()  # JWT-extended default message

    # Test accessing protected route with invalid token
    headers = {'Authorization': 'Bearer invalid_token'}
    response = client.get('/api/tasks', headers=headers)
    assert response.status_code == 422
    assert 'msg' in response.get_json()  # JWT-extended default message

def test_role_permissions(client, add_user):
    """Test role-based access control."""
    # Add users with different roles
    add_user('admin_user', 'password123', 'admin')
    add_user('ambulance_user', 'password123', 'ambulance')

    # Get tokens
    admin_response = client.post('/api/auth/login', json={
        'username': 'admin_user',
        'password': 'password123'
    })
    admin_token = admin_response.get_json()['data']['token']

    ambulance_response = client.post('/api/auth/login', json={
        'username': 'ambulance_user',
        'password': 'password123'
    })
    ambulance_token = ambulance_response.get_json()['data']['token']

    # Test admin-only routes
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    ambulance_headers = {'Authorization': f'Bearer {ambulance_token}'}

    # Test admin access to user list
    response = client.get('/api/auth/users', headers=admin_headers)
    assert response.status_code == 200
    response_data = response.get_json()
    assert 'message' in response_data
    assert 'data' in response_data
    assert isinstance(response_data['data'], list)

    # Test non-admin access to admin-only route
    response = client.get('/api/generate-report', headers=ambulance_headers)
    assert response.status_code == 403
    response_data = response.get_json()
    assert 'message' in response_data
    assert 'Access forbidden: Admins only' in response_data['message']

    # Test role-specific routes
    # Test admin access to user management
    response = client.get('/api/auth/users?role=ambulance', headers=admin_headers)
    assert response.status_code == 200
    response_data = response.get_json()
    assert 'data' in response_data
    assert isinstance(response_data['data'], list)

    # Test non-admin access to admin routes
    response = client.get('/api/auth/users', headers=ambulance_headers)
    assert response.status_code == 403
    response_data = response.get_json()
    assert 'message' in response_data
    assert 'Access forbidden: Admins only' in response_data['message'] 

def test_login(client, add_user):
    """
    Test user login:
    - Successful login with valid credentials
    - Login with invalid username
    - Login with invalid password
    - Login with missing fields
    """
    password = 'password123'

    # Add a test user to the database
    user = add_user('testuser', password, 'admin')

    # Step 1: Test successful login
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': password,
    })
    assert response.status_code == 200
    response_data = response.get_json()
    assert 'message' in response_data
    assert response_data['message'] == 'Login successful'
    assert 'data' in response_data
    assert 'token' in response_data['data']
    assert isinstance(response_data['data']['token'], str)

    # Step 2: Test login with an invalid username
    response = client.post('/api/auth/login', json={
        'username': 'nonexistentuser',
        'password': password,
    })
    assert response.status_code == 401
    response_data = response.get_json()
    assert response_data['message'] == 'Invalid username or password'

    # Step 3: Test login with an invalid password
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'wrongpassword',
    })
    assert response.status_code == 401
    response_data = response.get_json()
    assert response_data['message'] == 'Invalid username or password'

    # Step 4: Test login with missing username
    response = client.post('/api/auth/login', json={
        'password': password,
    })
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['message'] == 'Missing username or password'

    # Step 5: Test login with missing password
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
    })
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['message'] == 'Missing username or password'

    # Step 6: Test login with non-JSON request
    response = client.post('/api/auth/login', data='not json')
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['message'] == 'Missing JSON in request'
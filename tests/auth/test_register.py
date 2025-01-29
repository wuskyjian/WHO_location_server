import hashlib
from app.models import User

def test_register_user(client):
    """
    Test user registration:
    - Successful registration
    - Registration with an existing username
    - Registration with an invalid role
    """
    password = 'testpassword'
    
    # Step 1: Register a new user with a valid role
    response = client.post('/api/auth/register', json={
        'username': 'testuser',
        'password': password,
        'role': 'ambulance',
    })
    assert response.status_code == 201
    assert response.get_json()['message'] == 'User registered successfully'

    # Step 2: Attempt to register the same username again
    response = client.post('/api/auth/register', json={
        'username': 'testuser',
        'password': password,
        'role': 'ambulance',
    })
    assert response.status_code == 400
    assert response.get_json()['message'] == 'Username already exists'

    # Step 3: Attempt to register with an invalid role
    response = client.post('/api/auth/register', json={
        'username': 'invalidroleuser',
        'password': password,
        'role': 'invalid_role',
    })
    assert response.status_code == 400
    assert 'Invalid role' in response.get_json()['message']

    # Step 4: Validate the roles allowed for registration
    response = client.post('/api/auth/register', json={
        'username': 'cleaningteamuser',
        'password': password,
        'role': 'cleaning_team',
    })
    assert response.status_code == 201
    assert response.get_json()['message'] == 'User registered successfully' 
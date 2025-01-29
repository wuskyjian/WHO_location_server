import pytest
from app import db
from app.models import User

def test_get_users_by_role(client, add_user, login):
    """
    Test retrieving users by role:
    - Successful retrieval by an admin
    - Access forbidden for non-admin users
    - Ensure correct roles are filtered
    """
    # Step 1: Add users with different roles
    admin_user = add_user('adminuser', 'password123', 'admin')
    ambulance_user = add_user('ambulance_user', 'password123', 'ambulance')
    cleaning_team_user = add_user('cleaning_team_user', 'password123', 'cleaning_team')

    # Step 2: Admin logs in and retrieves users
    admin_token = login('adminuser', 'password123')
    
    # Test getting all non-admin users
    response = client.get('/api/auth/users', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    assert response.status_code == 200
    response_data = response.get_json()
    assert 'data' in response_data
    assert 'message' in response_data
    users = response_data['data']
    assert len(users) == 2  # Only ambulance and cleaning_team users
    usernames = [user['username'] for user in users]
    assert 'ambulance_user' in usernames
    assert 'cleaning_team_user' in usernames
    assert 'adminuser' not in usernames

    # Test getting ambulance users
    response = client.get('/api/auth/users?role=ambulance', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    assert response.status_code == 200
    response_data = response.get_json()
    users = response_data['data']
    assert len(users) == 1
    assert users[0]['username'] == 'ambulance_user'

    # Test getting cleaning team users
    response = client.get('/api/auth/users?role=cleaning_team', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    assert response.status_code == 200
    response_data = response.get_json()
    users = response_data['data']
    assert len(users) == 1
    assert users[0]['username'] == 'cleaning_team_user'

    # Step 3: Non-admin user attempts to retrieve users
    ambulance_token = login('ambulance_user', 'password123')
    response = client.get('/api/auth/users', headers={
        'Authorization': f'Bearer {ambulance_token}'
    })
    assert response.status_code == 403
    response_data = response.get_json()
    assert response_data['message'] == 'Access forbidden: Admins only'

def test_delete_user(client, add_user, login):
    """
    Test the delete_user route:
    - Successful deletion by an admin
    - Prevent deletion of non-existent users
    - Prevent admins from deleting themselves
    - Ensure only admins can delete users
    """
    # Step 1: Add users with different roles
    admin_user = add_user('adminuser', 'password123', 'admin')
    ambulance_user = add_user('ambulance_user', 'password123', 'ambulance')

    # Step 2: Admin deletes an ambulance user
    admin_token = login('adminuser', 'password123')
    response = client.delete(
        f'/api/auth/users/{ambulance_user.id}',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 200
    response_data = response.get_json()
    assert 'message' in response_data
    assert 'data' in response_data
    assert response_data['message'] == f'User {ambulance_user.id} deleted successfully'
    assert response_data['data']['deleted_id'] == ambulance_user.id

    # Verify the user has been deleted
    deleted_user = db.session.get(User, ambulance_user.id)
    assert deleted_user is None

    # Step 3: Attempt to delete a non-existent user
    response = client.delete(
        '/api/auth/users/9999',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 404
    response_data = response.get_json()
    assert response_data['message'] == 'User not found'

    # Step 4: Prevent an admin from deleting themselves
    response = client.delete(
        f'/api/auth/users/{admin_user.id}',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['message'] == 'Admins cannot delete themselves'

    # Step 5: Prevent a non-admin from deleting users
    non_admin_user = add_user('cleaning_user', 'password123', 'cleaning_team')
    non_admin_token = login('cleaning_user', 'password123')
    response = client.delete(
        f'/api/auth/users/{admin_user.id}',
        headers={'Authorization': f'Bearer {non_admin_token}'}
    )
    assert response.status_code == 403
    response_data = response.get_json()
    assert response_data['message'] == 'Access forbidden: Admins only' 
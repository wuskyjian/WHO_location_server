import pytest
from app import create_app, db
from app.models import User

@pytest.fixture(scope="function")
def app():
    """Create and configure a new app instance for each test."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key',
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def add_user(app):
    """Add a test user to the database."""
    def _add_user(username, password, role):
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    return _add_user

@pytest.fixture
def login(client):
    """Pytest fixture to log in a user and retrieve the JWT token."""
    def _login(username, password):
        response = client.post('/api/auth/login', json={
            'username': username,
            'password': password
        })
        assert response.status_code == 200, f"Login failed: {response.data}"
        response_data = response.get_json()
        assert 'data' in response_data, "Response missing data field"
        assert 'token' in response_data['data'], "Response missing token"
        return response_data['data']['token']
    return _login 
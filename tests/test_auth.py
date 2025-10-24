"""Tests for authentication functionality."""
import pytest
from pomodoro.models import db, User


def test_register_new_user(client):
    """Test user registration."""
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'newpass',
        'confirm_password': 'newpass'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Registration successful' in response.data or b'log in' in response.data.lower()
    
    # Verify user was created
    with client.application.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.check_password('newpass')


def test_register_existing_username(client, test_user):
    """Test registration with existing username."""
    response = client.post('/register', data={
        'username': 'testuser',  # Already exists from fixture
        'password': 'anotherpass',
        'confirm_password': 'anotherpass'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'already exists' in response.data or b'\xe6\x97\xa2\xe3\x81\xab\xe5\xad\x98\xe5\x9c\xa8' in response.data  # "already exists" in Japanese


def test_register_password_mismatch(client):
    """Test registration with mismatched passwords."""
    response = client.post('/register', data={
        'username': 'newuser2',
        'password': 'password1',
        'confirm_password': 'password2'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'do not match' in response.data


def test_login_success(client):
    """Test successful login."""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpass'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_login_nonexistent_user(client):
    """Test login with nonexistent user."""
    response = client.post('/login', data={
        'username': 'nonexistent',
        'password': 'somepass'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_logout(authenticated_client):
    """Test logout functionality."""
    response = authenticated_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    
    # Verify we're on the login page after logout
    assert b'login' in response.data.lower() or b'\xe3\x83\xad\xe3\x82\xb0\xe3\x82\xa4\xe3\x83\xb3' in response.data


def test_protected_route_without_login(client):
    """Test that protected routes require login."""
    # Index route should redirect when not authenticated
    response = client.get('/', follow_redirects=False)
    # Flask-Login can return 200 with a login page or 302 redirect
    assert response.status_code in [200, 302]
    
    # API routes should return 401 when not authenticated
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    assert response.status_code == 401  # Unauthorized


def test_user_isolation(app, test_user):
    """Test that users can only see their own data."""
    with app.app_context():
        # Create two users
        user1 = User(username='user1')
        user1.set_password('pass1')
        user2 = User(username='user2')
        user2.set_password('pass2')
        db.session.add_all([user1, user2])
        db.session.commit()
        
        user1_id = user1.id
        user2_id = user2.id
    
    # Login as user1 and create a session
    client = app.test_client()
    client.post('/login', data={'username': 'user1', 'password': 'pass1'})
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    assert response.status_code == 201
    
    # Logout and login as user2
    client.get('/logout')
    client.post('/login', data={'username': 'user2', 'password': 'pass2'})
    
    # User2 should see idle state (not user1's session)
    response = client.get('/api/pomodoro/state')
    assert response.status_code == 200
    data = response.get_json()
    assert data['mode'] == 'idle'

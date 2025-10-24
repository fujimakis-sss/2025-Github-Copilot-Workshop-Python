"""Shared test fixtures."""
import pytest
from app import create_app
from pomodoro.models import db, User


@pytest.fixture(scope='function')
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(app):
    """Create a test user for tests that need it."""
    with app.app_context():
        user = User(username='testuser')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def client(app):
    """Basic test client without authentication."""
    return app.test_client()


@pytest.fixture
def authenticated_client(app, test_user):
    """Client with logged in user."""
    client = app.test_client()
    with app.app_context():
        # Login the test user
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)
        yield client

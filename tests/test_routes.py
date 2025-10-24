"""Tests for API routes validation."""
import pytest
from app import create_app
from pomodoro.models import db


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_start_focus_valid_duration(client):
    """Test /start endpoint accepts valid duration."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['type'] == 'focus'


def test_start_focus_invalid_duration_zero(client):
    """Test /start endpoint rejects zero duration with 400."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 0})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'field' in data
    assert data['field'] == 'duration_minutes'
    assert 'at least 1 minute' in data['error']


def test_start_focus_invalid_duration_negative(client):
    """Test /start endpoint rejects negative duration with 400."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': -5})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'field' in data
    assert data['field'] == 'duration_minutes'


def test_start_focus_invalid_duration_too_high(client):
    """Test /start endpoint rejects duration above 240 with 400."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 241})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'field' in data
    assert data['field'] == 'duration_minutes'
    assert '240 minutes' in data['error']


def test_start_focus_boundary_min(client):
    """Test /start endpoint accepts minimum valid duration (1)."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 1})
    assert response.status_code == 201


def test_start_focus_boundary_max(client):
    """Test /start endpoint accepts maximum valid duration (240)."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 240})
    assert response.status_code == 201


def test_start_break_valid_duration(client):
    """Test /break endpoint accepts valid duration."""
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 5})
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['type'] == 'break'


def test_start_break_invalid_duration_zero(client):
    """Test /break endpoint rejects zero duration with 400."""
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 0})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'field' in data
    assert data['field'] == 'duration_minutes'
    assert 'at least 1 minute' in data['error']


def test_start_break_invalid_duration_too_high(client):
    """Test /break endpoint rejects duration above 240 with 400."""
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 300})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'field' in data
    assert data['field'] == 'duration_minutes'
    assert '240 minutes' in data['error']


def test_start_break_boundary_min(client):
    """Test /break endpoint accepts minimum valid duration (1)."""
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 1})
    assert response.status_code == 201


def test_start_break_boundary_max(client):
    """Test /break endpoint accepts maximum valid duration (240)."""
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 240})
    assert response.status_code == 201


def test_start_focus_default_duration(client):
    """Test /start endpoint uses default duration when not provided."""
    response = client.post('/api/pomodoro/start', json={})
    assert response.status_code == 201


def test_start_break_default_duration(client):
    """Test /break endpoint uses default duration when not provided."""
    response = client.post('/api/pomodoro/break', json={})
    assert response.status_code == 201

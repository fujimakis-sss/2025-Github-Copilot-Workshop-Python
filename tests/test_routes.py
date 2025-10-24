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
    with app.app_context():
        yield app.test_client()
        # Clean up any active sessions after each test
        db.session.rollback()


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


def test_get_state_idle(client):
    """Test /state endpoint returns idle when no active session."""
    response = client.get('/api/pomodoro/state')
    assert response.status_code == 200
    data = response.get_json()
    assert data['mode'] == 'idle'
    assert data['remaining_seconds'] == 0
    assert 'completed_focus_count' in data
    assert 'total_focus_seconds' in data


def test_get_state_active_focus(client):
    """Test /state endpoint returns focus mode when focus session is active."""
    # Start a focus session
    client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    
    # Get state
    response = client.get('/api/pomodoro/state')
    assert response.status_code == 200
    data = response.get_json()
    assert data['mode'] == 'focus'
    assert data['remaining_seconds'] > 0
    assert data['remaining_seconds'] <= 1500  # 25 minutes


def test_get_state_active_break(client):
    """Test /state endpoint returns break mode when break session is active."""
    # Start a break session
    client.post('/api/pomodoro/break', json={'duration_minutes': 5})
    
    # Get state
    response = client.get('/api/pomodoro/state')
    assert response.status_code == 200
    data = response.get_json()
    assert data['mode'] == 'break'
    assert data['remaining_seconds'] > 0
    assert data['remaining_seconds'] <= 300  # 5 minutes


def test_stop_endpoint(client):
    """Test /stop endpoint successfully stops active session."""
    # Start a focus session
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    assert response.status_code == 201
    
    # Stop the session
    response = client.post('/api/pomodoro/stop')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'stopped'
    
    # Verify state is idle
    response = client.get('/api/pomodoro/state')
    data = response.get_json()
    assert data['mode'] == 'idle'


def test_stop_when_no_active_session(client):
    """Test /stop endpoint handles no active session gracefully."""
    response = client.post('/api/pomodoro/stop')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'stopped'


def test_conflict_focus_when_focus_active(client):
    """Test starting focus when focus is already active returns conflict."""
    # Start first focus
    client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    
    # Try to start another focus
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    assert response.status_code == 409
    data = response.get_json()
    assert 'error' in data


def test_conflict_break_when_focus_active(client):
    """Test starting break when focus is active returns conflict."""
    # Start focus
    client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    
    # Try to start break
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 5})
    assert response.status_code == 409
    data = response.get_json()
    assert 'error' in data


def test_conflict_focus_when_break_active(client):
    """Test starting focus when break is active returns conflict."""
    # Start break
    client.post('/api/pomodoro/break', json={'duration_minutes': 5})
    
    # Try to start focus
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    assert response.status_code == 409
    data = response.get_json()
    assert 'error' in data


def test_start_focus_missing_json_body(client):
    """Test /start endpoint handles missing JSON body gracefully."""
    response = client.post('/api/pomodoro/start', 
                          data='',
                          content_type='application/json')
    assert response.status_code == 201  # Should use default


def test_start_break_missing_json_body(client):
    """Test /break endpoint handles missing JSON body gracefully."""
    response = client.post('/api/pomodoro/break',
                          data='',
                          content_type='application/json')
    assert response.status_code == 201  # Should use default


def test_start_focus_invalid_json(client):
    """Test /start endpoint handles invalid JSON gracefully."""
    response = client.post('/api/pomodoro/start',
                          data='invalid json',
                          content_type='application/json')
    assert response.status_code == 201  # Should use default due to silent=True


def test_start_focus_returns_correct_session_data(client):
    """Test /start endpoint returns complete session data."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 30})
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert 'type' in data
    assert data['type'] == 'focus'
    assert 'planned_end_at' in data


def test_start_break_returns_correct_session_data(client):
    """Test /break endpoint returns complete session data."""
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 10})
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert 'type' in data
    assert data['type'] == 'break'
    assert 'planned_end_at' in data

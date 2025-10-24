"""Tests for preset functionality."""
import pytest
from app import create_app
from pomodoro.models import db
from config import Config


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


def test_config_has_presets():
    """Test that Config has POMODORO_PRESETS defined."""
    assert hasattr(Config, 'POMODORO_PRESETS')
    assert isinstance(Config.POMODORO_PRESETS, dict)
    assert 'default' in Config.POMODORO_PRESETS
    assert 'long' in Config.POMODORO_PRESETS
    assert 'short' in Config.POMODORO_PRESETS


def test_default_preset_values():
    """Test that default preset has expected values."""
    default_preset = Config.POMODORO_PRESETS['default']
    assert default_preset['focus'] == 25
    assert default_preset['break'] == 5


def test_long_preset_values():
    """Test that long preset has expected values."""
    long_preset = Config.POMODORO_PRESETS['long']
    assert long_preset['focus'] == 50
    assert long_preset['break'] == 10


def test_short_preset_values():
    """Test that short preset has expected values."""
    short_preset = Config.POMODORO_PRESETS['short']
    assert short_preset['focus'] == 15
    assert short_preset['break'] == 3


def test_start_with_default_preset(client):
    """Test starting a focus session with default preset duration."""
    # Ensure no active session exists
    client.post('/api/pomodoro/stop')
    
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    assert response.status_code == 201
    data = response.get_json()
    assert data['type'] == 'focus'


def test_start_with_long_preset(client):
    """Test starting a focus session with long preset duration."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 50})
    assert response.status_code == 201
    data = response.get_json()
    assert data['type'] == 'focus'


def test_start_with_short_preset(client):
    """Test starting a focus session with short preset duration."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 15})
    assert response.status_code == 201
    data = response.get_json()
    assert data['type'] == 'focus'


def test_break_with_default_preset(client):
    """Test starting a break session with default preset duration."""
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 5})
    assert response.status_code == 201
    data = response.get_json()
    assert data['type'] == 'break'


def test_break_with_long_preset(client):
    """Test starting a break session with long preset duration."""
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 10})
    assert response.status_code == 201
    data = response.get_json()
    assert data['type'] == 'break'


def test_break_with_short_preset(client):
    """Test starting a break session with short preset duration."""
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 3})
    assert response.status_code == 201
    data = response.get_json()
    assert data['type'] == 'break'


def test_state_includes_planned_duration(client):
    """Test that state response includes planned_duration_sec."""
    # Start a session
    client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    
    # Get state
    response = client.get('/api/pomodoro/state')
    assert response.status_code == 200
    data = response.get_json()
    
    assert 'planned_duration_sec' in data
    assert data['planned_duration_sec'] == 25 * 60


def test_custom_duration_still_works(client):
    """Test that custom duration values still work alongside presets."""
    # Test a custom value not matching any preset
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 30})
    assert response.status_code == 201
    data = response.get_json()
    assert data['type'] == 'focus'

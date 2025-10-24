import pytest
from app import create_app
from pomodoro.models import db
from pomodoro.services import start_focus, start_break, stop_active_session, get_state


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
def app_context(app):
    with app.app_context():
        yield


def test_start_focus_and_state(app_context):
    session = start_focus(1)  # 1分
    assert session.id is not None
    assert session.type == 'focus'
    
    state = get_state()
    assert state['mode'] == 'focus'
    assert state['remaining_seconds'] <= 60
    
    stop_active_session()
    state2 = get_state()
    assert state2['mode'] == 'idle'


def test_start_break_conflict(app_context):
    start_focus(1)
    with pytest.raises(ValueError):
        start_break(1)
    stop_active_session()


def test_start_focus_invalid_duration_too_low(app_context):
    """Test that start_focus rejects duration below minimum."""
    with pytest.raises(ValueError, match="Duration must be at least 1 minute"):
        start_focus(0)


def test_start_focus_invalid_duration_negative(app_context):
    """Test that start_focus rejects negative duration."""
    with pytest.raises(ValueError, match="Duration must be at least 1 minute"):
        start_focus(-5)


def test_start_focus_invalid_duration_too_high(app_context):
    """Test that start_focus rejects duration above maximum."""
    with pytest.raises(ValueError, match="Duration must be at most 240 minutes"):
        start_focus(241)


def test_start_focus_valid_duration_boundaries(app_context):
    """Test that start_focus accepts valid boundary durations."""
    session = start_focus(1)  # Minimum valid
    assert session.id is not None
    stop_active_session()
    
    session2 = start_focus(240)  # Maximum valid
    assert session2.id is not None
    stop_active_session()


def test_start_break_invalid_duration_too_low(app_context):
    """Test that start_break rejects duration below minimum."""
    with pytest.raises(ValueError, match="Duration must be at least 1 minute"):
        start_break(0)


def test_start_break_invalid_duration_too_high(app_context):
    """Test that start_break rejects duration above maximum."""
    with pytest.raises(ValueError, match="Duration must be at most 240 minutes"):
        start_break(300)


def test_start_break_valid_duration_boundaries(app_context):
    """Test that start_break accepts valid boundary durations."""
    session = start_break(1)  # Minimum valid
    assert session.id is not None
    stop_active_session()
    
    session2 = start_break(240)  # Maximum valid
    assert session2.id is not None
    stop_active_session()


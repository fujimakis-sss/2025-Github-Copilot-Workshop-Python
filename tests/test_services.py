import pytest
from flask import session
from flask_login import login_user
from app import create_app
from pomodoro.models import db, User
from pomodoro.services import start_focus, start_break, stop_active_session, get_state


@pytest.fixture
def authenticated_app_context(app):
    """Provides app context with authenticated user in a test request context."""
    with app.test_request_context():
        with app.app_context():
            # Get the test user and login
            user = User.query.filter_by(username='testuser').first()
            login_user(user)
            yield
            db.session.rollback()


def test_start_focus_and_state(authenticated_app_context):
    session = start_focus(1)  # 1分
    assert session.id is not None
    assert session.type == 'focus'
    
    state = get_state()
    assert state['mode'] == 'focus'
    assert state['remaining_seconds'] <= 60
    
    stop_active_session()
    state2 = get_state()
    assert state2['mode'] == 'idle'


def test_start_break_conflict(authenticated_app_context):
    start_focus(1)
    with pytest.raises(ValueError):
        start_break(1)
    stop_active_session()


def test_start_focus_invalid_duration_too_low(authenticated_app_context):
    """Test that start_focus rejects duration below minimum."""
    with pytest.raises(ValueError, match="Duration must be at least 1 minute"):
        start_focus(0)


def test_start_focus_invalid_duration_negative(authenticated_app_context):
    """Test that start_focus rejects negative duration."""
    with pytest.raises(ValueError, match="Duration must be at least 1 minute"):
        start_focus(-5)


def test_start_focus_invalid_duration_too_high(authenticated_app_context):
    """Test that start_focus rejects duration above maximum."""
    with pytest.raises(ValueError, match="Duration must be at most 240 minutes"):
        start_focus(241)


def test_start_focus_valid_duration_boundaries(authenticated_app_context):
    """Test that start_focus accepts valid boundary durations."""
    session = start_focus(1)  # Minimum valid
    assert session.id is not None
    stop_active_session()
    
    session2 = start_focus(240)  # Maximum valid
    assert session2.id is not None
    stop_active_session()


def test_start_break_invalid_duration_too_low(authenticated_app_context):
    """Test that start_break rejects duration below minimum."""
    with pytest.raises(ValueError, match="Duration must be at least 1 minute"):
        start_break(0)


def test_start_break_invalid_duration_too_high(authenticated_app_context):
    """Test that start_break rejects duration above maximum."""
    with pytest.raises(ValueError, match="Duration must be at most 240 minutes"):
        start_break(300)


def test_start_break_valid_duration_boundaries(authenticated_app_context):
    """Test that start_break accepts valid boundary durations."""
    session = start_break(1)  # Minimum valid
    assert session.id is not None
    stop_active_session()
    
    session2 = start_break(240)  # Maximum valid
    assert session2.id is not None
    stop_active_session()


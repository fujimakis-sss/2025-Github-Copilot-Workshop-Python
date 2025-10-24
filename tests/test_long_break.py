"""Tests for long break suggestion feature."""
import pytest
from app import create_app
from pomodoro.models import db, DailyStat
from pomodoro.services import (
    start_focus, 
    complete_session, 
    get_state, 
    start_long_break, 
    decline_long_break,
    stop_active_session
)
from datetime import datetime, timezone


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


@pytest.fixture
def client(app):
    with app.app_context():
        yield app.test_client()
        db.session.rollback()


def test_cycle_count_increments_on_focus_completion(app_context):
    """Test that cycle_count increments when a focus session completes."""
    session = start_focus(1)
    complete_session(session.id)
    
    state = get_state()
    assert state['cycle_count'] == 1


def test_cycle_count_tracks_multiple_sessions(app_context):
    """Test that cycle_count correctly tracks multiple focus sessions."""
    for i in range(3):
        session = start_focus(1)
        complete_session(session.id)
    
    state = get_state()
    assert state['cycle_count'] == 3
    assert state['completed_focus_count'] == 3


def test_long_break_suggested_after_4_sessions(app_context):
    """Test that long break is suggested after 4 focus sessions."""
    # Complete 3 sessions - should not suggest
    for i in range(3):
        session = start_focus(1)
        complete_session(session.id)
    
    state = get_state()
    assert state['cycle_count'] == 3
    assert state['suggest_long_break'] is False
    
    # Complete 4th session - should suggest
    session = start_focus(1)
    complete_session(session.id)
    
    state = get_state()
    assert state['cycle_count'] == 4
    assert state['suggest_long_break'] is True


def test_long_break_not_suggested_when_session_active(app_context):
    """Test that long break is not suggested while a session is active."""
    # Complete 4 sessions
    for i in range(4):
        session = start_focus(1)
        complete_session(session.id)
    
    # Start a new session
    start_focus(1)
    
    state = get_state()
    assert state['cycle_count'] == 4
    assert state['mode'] == 'focus'
    assert state['suggest_long_break'] is False  # Not idle


def test_start_long_break_resets_cycle(app_context):
    """Test that starting a long break resets the cycle count."""
    # Complete 4 sessions
    for i in range(4):
        session = start_focus(1)
        complete_session(session.id)
    
    state = get_state()
    assert state['cycle_count'] == 4
    
    # Start long break
    long_break = start_long_break()
    assert long_break.type == 'break'
    assert long_break.planned_duration_sec == 15 * 60
    
    # Verify cycle reset
    today = datetime.now(timezone.utc).date()
    stat = DailyStat.query.filter_by(date=today).first()
    assert stat.cycle_count == 0


def test_decline_long_break_resets_cycle(app_context):
    """Test that declining a long break resets the cycle count."""
    # Complete 4 sessions
    for i in range(4):
        session = start_focus(1)
        complete_session(session.id)
    
    state = get_state()
    assert state['cycle_count'] == 4
    
    # Decline long break
    decline_long_break()
    
    # Verify cycle reset
    state = get_state()
    assert state['cycle_count'] == 0
    assert state['suggest_long_break'] is False


def test_cycle_persists_across_state_calls(app_context):
    """Test that cycle_count persists across multiple get_state calls."""
    session = start_focus(1)
    complete_session(session.id)
    
    state1 = get_state()
    assert state1['cycle_count'] == 1
    
    state2 = get_state()
    assert state2['cycle_count'] == 1


def test_regular_break_does_not_reset_cycle(app_context):
    """Test that a regular break does not reset the cycle count."""
    # Complete 2 sessions
    for i in range(2):
        session = start_focus(1)
        complete_session(session.id)
    
    # Take a regular break
    from pomodoro.services import start_break
    break_session = start_break(5)
    complete_session(break_session.id)
    
    # Cycle should still be 2
    state = get_state()
    assert state['cycle_count'] == 2


def test_long_break_api_endpoint(client):
    """Test POST /api/pomodoro/long-break endpoint."""
    # Complete 4 sessions
    for i in range(4):
        response = client.post('/api/pomodoro/start', json={'duration_minutes': 1})
        assert response.status_code == 201
        data = response.get_json()
        # Manually complete the session
        from pomodoro.services import complete_session
        complete_session(data['id'])
    
    # Start long break via API
    response = client.post('/api/pomodoro/long-break')
    assert response.status_code == 201
    data = response.get_json()
    assert data['type'] == 'break'
    assert data['duration_minutes'] == 15
    
    # Verify cycle reset
    state_response = client.get('/api/pomodoro/state')
    state = state_response.get_json()
    assert state['cycle_count'] == 0


def test_decline_long_break_api_endpoint(client):
    """Test POST /api/pomodoro/decline-long-break endpoint."""
    # Complete 4 sessions
    for i in range(4):
        response = client.post('/api/pomodoro/start', json={'duration_minutes': 1})
        assert response.status_code == 201
        data = response.get_json()
        from pomodoro.services import complete_session
        complete_session(data['id'])
    
    # Decline long break via API
    response = client.post('/api/pomodoro/decline-long-break')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'declined'
    
    # Verify cycle reset
    state_response = client.get('/api/pomodoro/state')
    state = state_response.get_json()
    assert state['cycle_count'] == 0


def test_state_includes_cycle_info(client):
    """Test that GET /api/pomodoro/state includes cycle information."""
    response = client.get('/api/pomodoro/state')
    assert response.status_code == 200
    data = response.get_json()
    
    assert 'cycle_count' in data
    assert 'suggest_long_break' in data
    assert data['cycle_count'] == 0
    assert data['suggest_long_break'] is False


def test_long_break_cannot_start_with_active_session(client):
    """Test that long break cannot start if there's an active session."""
    # Start a focus session
    client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    
    # Try to start long break
    response = client.post('/api/pomodoro/long-break')
    assert response.status_code == 409
    data = response.get_json()
    assert 'error' in data


def test_cycle_count_in_daily_stat_model(app_context):
    """Test that DailyStat model includes cycle_count field."""
    today = datetime.now(timezone.utc).date()
    stat = DailyStat(date=today, total_focus_seconds=1500, completed_focus_count=1, cycle_count=1)
    db.session.add(stat)
    db.session.commit()
    
    retrieved = DailyStat.query.filter_by(date=today).first()
    assert retrieved.cycle_count == 1
    
    stat_dict = retrieved.to_dict()
    assert 'cycle_count' in stat_dict
    assert stat_dict['cycle_count'] == 1

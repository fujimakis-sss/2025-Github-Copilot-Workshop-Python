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


def test_stop_active_session_idempotent(app_context):
    """Test that calling stop_active_session multiple times is safe."""
    session = start_focus(25)
    assert session.status == 'active'
    
    stop_active_session()
    stop_active_session()  # Should not raise
    stop_active_session()  # Should not raise


def test_complete_session_marks_focus_completed(app_context):
    """Test that complete_session marks focus session as completed."""
    from pomodoro.services import complete_session
    session = start_focus(1)
    session_id = session.id
    
    complete_session(session_id)
    
    from pomodoro.models import PomodoroSession
    completed = PomodoroSession.query.get(session_id)
    assert completed.status == 'completed'
    assert completed.end_at is not None


def test_complete_session_updates_daily_stats_for_focus(app_context):
    """Test that completing focus session updates daily statistics."""
    from pomodoro.services import complete_session
    from pomodoro.models import DailyStat
    from datetime import datetime, timezone
    
    session = start_focus(25)
    session_id = session.id
    
    # Complete the session
    complete_session(session_id)
    
    # Check daily stats were updated
    today = datetime.now(timezone.utc).date()
    stat = DailyStat.query.filter_by(date=today).first()
    assert stat is not None
    assert stat.completed_focus_count == 1
    assert stat.total_focus_seconds == 25 * 60


def test_complete_session_does_not_update_stats_for_break(app_context):
    """Test that completing break session does not update stats."""
    from pomodoro.services import complete_session
    from pomodoro.models import DailyStat
    from datetime import datetime, timezone
    
    session = start_break(5)
    session_id = session.id
    
    # Complete the session
    complete_session(session_id)
    
    # Check daily stats were NOT created/updated
    today = datetime.now(timezone.utc).date()
    stat = DailyStat.query.filter_by(date=today).first()
    assert stat is None or stat.completed_focus_count == 0


def test_complete_session_ignores_invalid_id(app_context):
    """Test that complete_session handles invalid session ID gracefully."""
    from pomodoro.services import complete_session
    # Should not raise
    complete_session(99999)


def test_complete_session_ignores_non_active_session(app_context):
    """Test that complete_session only completes active sessions."""
    from pomodoro.services import complete_session
    from pomodoro.models import PomodoroSession
    
    session = start_focus(1)
    session_id = session.id
    stop_active_session()  # Mark as aborted
    
    # Try to complete - should be ignored
    complete_session(session_id)
    
    completed = PomodoroSession.query.get(session_id)
    assert completed.status == 'aborted'  # Still aborted, not completed


def test_get_state_auto_completes_expired_session(app_context):
    """Test that get_state auto-completes sessions past their end time."""
    from datetime import datetime, timedelta, timezone
    from pomodoro.models import PomodoroSession, db
    
    # Manually create an expired session
    now = datetime.now(timezone.utc)
    expired_session = PomodoroSession(
        type='focus',
        planned_duration_sec=1,
        start_at=now - timedelta(seconds=10),
        planned_end_at=now - timedelta(seconds=5),  # Ended 5 seconds ago
        status='active'
    )
    db.session.add(expired_session)
    db.session.commit()
    
    # Get state should auto-complete
    state = get_state()
    assert state['mode'] == 'idle'
    assert state['remaining_seconds'] == 0
    
    # Verify session was marked as completed
    from pomodoro.models import PomodoroSession
    session = PomodoroSession.query.get(expired_session.id)
    assert session.status == 'completed'


def test_multiple_completed_focus_sessions_accumulate_stats(app_context):
    """Test that multiple completed focus sessions accumulate in daily stats."""
    from pomodoro.services import complete_session
    from pomodoro.models import DailyStat
    from datetime import datetime, timezone
    
    # Complete first focus
    session1 = start_focus(25)
    complete_session(session1.id)
    
    # Complete second focus
    session2 = start_focus(30)
    complete_session(session2.id)
    
    # Check accumulated stats
    today = datetime.now(timezone.utc).date()
    stat = DailyStat.query.filter_by(date=today).first()
    assert stat.completed_focus_count == 2
    assert stat.total_focus_seconds == (25 + 30) * 60


def test_start_focus_conflict_with_break(app_context):
    """Test that starting focus while break is active raises error."""
    start_break(5)
    with pytest.raises(ValueError, match="Active session already exists"):
        start_focus(25)


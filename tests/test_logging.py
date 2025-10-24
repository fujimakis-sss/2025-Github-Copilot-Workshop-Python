import pytest
import json
import logging
from io import StringIO
from app import create_app
from pomodoro.models import db
from pomodoro.services import start_focus, start_break, stop_active_session, complete_session


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
def log_capture():
    """Capture log output for testing."""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    
    # Get the root logger used by services
    logger = logging.getLogger('pomodoro.services')
    original_handlers = logger.handlers[:]
    logger.handlers = [handler]
    
    # Import JsonFormatter from app
    from app import JsonFormatter
    handler.setFormatter(JsonFormatter())
    
    yield log_stream
    
    # Restore original handlers
    logger.handlers = original_handlers


def test_start_focus_logs_session_start(app_context, log_capture):
    """Test that start_focus logs a session_start event."""
    session = start_focus(25)
    
    log_output = log_capture.getvalue()
    assert log_output, "No log output captured"
    
    log_lines = log_output.strip().split('\n')
    log_entry = json.loads(log_lines[-1])
    
    assert log_entry['event'] == 'session_start'
    assert log_entry['session_id'] == session.id
    assert log_entry['type'] == 'focus'
    assert log_entry['duration'] == 1500  # 25 minutes * 60 seconds
    assert 'timestamp' in log_entry
    assert log_entry['timestamp'].endswith('Z')


def test_start_break_logs_session_start(app_context, log_capture):
    """Test that start_break logs a session_start event."""
    session = start_break(5)
    
    log_output = log_capture.getvalue()
    assert log_output, "No log output captured"
    
    log_lines = log_output.strip().split('\n')
    log_entry = json.loads(log_lines[-1])
    
    assert log_entry['event'] == 'session_start'
    assert log_entry['session_id'] == session.id
    assert log_entry['type'] == 'break'
    assert log_entry['duration'] == 300  # 5 minutes * 60 seconds
    assert 'timestamp' in log_entry


def test_stop_active_session_logs_session_stop(app_context, log_capture):
    """Test that stop_active_session logs a session_stop event."""
    session = start_focus(1)
    log_capture.truncate(0)  # Clear previous logs
    log_capture.seek(0)
    
    stop_active_session()
    
    log_output = log_capture.getvalue()
    assert log_output, "No log output captured"
    
    log_lines = log_output.strip().split('\n')
    log_entry = json.loads(log_lines[-1])
    
    assert log_entry['event'] == 'session_stop'
    assert log_entry['session_id'] == session.id
    assert log_entry['type'] == 'focus'
    assert log_entry['status'] == 'aborted'
    assert 'timestamp' in log_entry


def test_complete_session_logs_session_complete(app_context, log_capture):
    """Test that complete_session logs a session_complete event."""
    session = start_focus(1)
    log_capture.truncate(0)  # Clear previous logs
    log_capture.seek(0)
    
    complete_session(session.id)
    
    log_output = log_capture.getvalue()
    assert log_output, "No log output captured"
    
    log_lines = log_output.strip().split('\n')
    log_entry = json.loads(log_lines[-1])
    
    assert log_entry['event'] == 'session_complete'
    assert log_entry['session_id'] == session.id
    assert log_entry['type'] == 'focus'
    assert log_entry['duration'] == 60  # 1 minute * 60 seconds
    assert log_entry['status'] == 'completed'
    assert 'timestamp' in log_entry


def test_log_level_configuration(app):
    """Test that LOG_LEVEL configuration is respected."""
    # Default is INFO
    assert app.config['LOG_LEVEL'] == 'INFO'

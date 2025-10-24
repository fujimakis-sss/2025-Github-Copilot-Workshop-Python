"""Tests for SocketIO WebSocket functionality."""
import pytest
from flask_socketio import SocketIOTestClient
from app import create_app
from pomodoro.models import db


@pytest.fixture
def app():
    test_app = create_app()
    test_app.config['TESTING'] = True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    with app.app_context():
        yield app.test_client()


@pytest.fixture
def socketio_client(app):
    """Create a SocketIO test client."""
    from app import socketio
    with app.app_context():
        return socketio.test_client(app, namespace='/')


def test_socketio_connect(socketio_client):
    """Test that client can connect to SocketIO server."""
    assert socketio_client.is_connected()


def test_state_update_on_start_focus(app, client, socketio_client):
    """Test that state_update event is emitted when focus session starts."""
    # Start a focus session
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    assert response.status_code == 201
    
    # Check if state_update event was received
    received = socketio_client.get_received()
    assert len(received) > 0
    
    # Find the state_update event
    state_update_found = False
    for event in received:
        if event['name'] == 'state_update':
            state_update_found = True
            data = event['args'][0]
            assert data['mode'] == 'focus'
            assert data['remaining_seconds'] > 0
            break
    
    assert state_update_found, "state_update event not received"


def test_state_update_on_start_break(app, client, socketio_client):
    """Test that state_update event is emitted when break session starts."""
    # Start a break session
    response = client.post('/api/pomodoro/break', json={'duration_minutes': 5})
    assert response.status_code == 201
    
    # Check if state_update event was received
    received = socketio_client.get_received()
    assert len(received) > 0
    
    # Find the state_update event
    state_update_found = False
    for event in received:
        if event['name'] == 'state_update':
            state_update_found = True
            data = event['args'][0]
            assert data['mode'] == 'break'
            assert data['remaining_seconds'] > 0
            break
    
    assert state_update_found, "state_update event not received"


def test_state_update_on_stop(app, client, socketio_client):
    """Test that state_update event is emitted when session is stopped."""
    # Start a focus session first
    client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    socketio_client.get_received()  # Clear previous events
    
    # Stop the session
    response = client.post('/api/pomodoro/stop')
    assert response.status_code == 200
    
    # Check if state_update event was received
    received = socketio_client.get_received()
    assert len(received) > 0
    
    # Find the state_update event
    state_update_found = False
    for event in received:
        if event['name'] == 'state_update':
            state_update_found = True
            data = event['args'][0]
            assert data['mode'] == 'idle'
            assert data['remaining_seconds'] == 0
            break
    
    assert state_update_found, "state_update event not received"


def test_multiple_clients_receive_updates(app, client):
    """Test that multiple connected clients receive state updates."""
    from app import socketio
    
    # Create two SocketIO clients
    with app.app_context():
        client1 = socketio.test_client(app, namespace='/')
        client2 = socketio.test_client(app, namespace='/')
        
        assert client1.is_connected()
        assert client2.is_connected()
        
        # Start a focus session
        response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
        assert response.status_code == 201
        
        # Both clients should receive the state_update event
        received1 = client1.get_received()
        received2 = client2.get_received()
        
        assert len(received1) > 0
        assert len(received2) > 0
        
        # Verify both received state_update events
        for received in [received1, received2]:
            state_update_found = False
            for event in received:
                if event['name'] == 'state_update':
                    state_update_found = True
                    data = event['args'][0]
                    assert data['mode'] == 'focus'
                    break
            assert state_update_found


def test_state_update_structure(app, client, socketio_client):
    """Test that state_update event has correct structure."""
    # Start a focus session
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    assert response.status_code == 201
    
    # Get state_update event
    received = socketio_client.get_received()
    state_update_event = None
    for event in received:
        if event['name'] == 'state_update':
            state_update_event = event
            break
    
    assert state_update_event is not None
    data = state_update_event['args'][0]
    
    # Verify required fields
    assert 'mode' in data
    assert 'remaining_seconds' in data
    assert 'completed_focus_count' in data
    assert 'total_focus_seconds' in data
    
    # Verify types
    assert isinstance(data['mode'], str)
    assert isinstance(data['remaining_seconds'], int)
    assert isinstance(data['completed_focus_count'], int)
    assert isinstance(data['total_focus_seconds'], int)

"""API contract tests for Pomodoro API endpoints.

These tests verify the API contract - ensuring that responses match expected schemas
and that API behavior remains consistent across versions.
"""
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
        db.session.rollback()


class TestStartFocusContract:
    """Contract tests for POST /api/pomodoro/start endpoint."""
    
    def test_success_response_structure(self, client):
        """Verify success response contains required fields with correct types."""
        response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
        assert response.status_code == 201
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'id' in data
        assert 'type' in data
        assert 'planned_end_at' in data
        
        assert isinstance(data['id'], int)
        assert isinstance(data['type'], str)
        assert isinstance(data['planned_end_at'], str)
        assert data['type'] == 'focus'
    
    def test_error_response_structure(self, client):
        """Verify error response contains required fields with correct types."""
        response = client.post('/api/pomodoro/start', json={'duration_minutes': 0})
        assert response.status_code == 400
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'error' in data
        assert 'field' in data
        
        assert isinstance(data['error'], str)
        assert isinstance(data['field'], str)
    
    def test_conflict_response_structure(self, client):
        """Verify conflict response contains required fields."""
        client.post('/api/pomodoro/start', json={'duration_minutes': 25})
        response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
        
        assert response.status_code == 409
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'error' in data
        assert isinstance(data['error'], str)
    
    def test_planned_end_at_is_iso8601(self, client):
        """Verify planned_end_at is in ISO 8601 format."""
        from datetime import datetime
        response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
        data = response.get_json()
        
        # Should be parseable as ISO 8601
        planned_end = datetime.fromisoformat(data['planned_end_at'].replace('Z', '+00:00'))
        assert planned_end is not None


class TestStartBreakContract:
    """Contract tests for POST /api/pomodoro/break endpoint."""
    
    def test_success_response_structure(self, client):
        """Verify success response contains required fields with correct types."""
        response = client.post('/api/pomodoro/break', json={'duration_minutes': 5})
        assert response.status_code == 201
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'id' in data
        assert 'type' in data
        assert 'planned_end_at' in data
        
        assert isinstance(data['id'], int)
        assert isinstance(data['type'], str)
        assert isinstance(data['planned_end_at'], str)
        assert data['type'] == 'break'
    
    def test_error_response_structure(self, client):
        """Verify error response contains required fields with correct types."""
        response = client.post('/api/pomodoro/break', json={'duration_minutes': 500})
        assert response.status_code == 400
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'error' in data
        assert 'field' in data


class TestStopContract:
    """Contract tests for POST /api/pomodoro/stop endpoint."""
    
    def test_response_structure(self, client):
        """Verify response contains required fields with correct types."""
        response = client.post('/api/pomodoro/stop')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'status' in data
        assert isinstance(data['status'], str)
        assert data['status'] == 'stopped'


class TestStateContract:
    """Contract tests for GET /api/pomodoro/state endpoint."""
    
    def test_idle_state_structure(self, client):
        """Verify idle state response contains all required fields."""
        response = client.get('/api/pomodoro/state')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert isinstance(data, dict)
        
        # Required fields
        assert 'mode' in data
        assert 'remaining_seconds' in data
        assert 'completed_focus_count' in data
        assert 'total_focus_seconds' in data
        
        # Type checking
        assert isinstance(data['mode'], str)
        assert isinstance(data['remaining_seconds'], int)
        assert isinstance(data['completed_focus_count'], int)
        assert isinstance(data['total_focus_seconds'], int)
        
        # Value validation for idle
        assert data['mode'] == 'idle'
        assert data['remaining_seconds'] == 0
    
    def test_active_focus_state_structure(self, client):
        """Verify active focus state response contains all required fields."""
        client.post('/api/pomodoro/start', json={'duration_minutes': 25})
        response = client.get('/api/pomodoro/state')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['mode'] == 'focus'
        assert data['remaining_seconds'] > 0
        assert isinstance(data['completed_focus_count'], int)
        assert isinstance(data['total_focus_seconds'], int)
    
    def test_active_break_state_structure(self, client):
        """Verify active break state response contains all required fields."""
        client.post('/api/pomodoro/break', json={'duration_minutes': 5})
        response = client.get('/api/pomodoro/state')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['mode'] == 'break'
        assert data['remaining_seconds'] > 0


class TestHealthContract:
    """Contract tests for GET /health endpoint."""
    
    def test_health_response_structure(self, client):
        """Verify health check response structure."""
        response = client.get('/health')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'status' in data
        assert data['status'] == 'ok'


class TestAPIVersionConsistency:
    """Tests to ensure API behavior remains consistent."""
    
    def test_all_endpoints_return_json(self, client):
        """Verify all API endpoints return JSON content type."""
        endpoints = [
            ('POST', '/api/pomodoro/start', {'duration_minutes': 25}),
            ('POST', '/api/pomodoro/break', {'duration_minutes': 5}),
            ('POST', '/api/pomodoro/stop', None),
            ('GET', '/api/pomodoro/state', None),
            ('GET', '/health', None),
        ]
        
        for method, url, data in endpoints:
            if method == 'POST':
                if data:
                    response = client.post(url, json=data)
                else:
                    response = client.post(url)
            else:
                response = client.get(url)
            
            assert response.content_type == 'application/json', \
                f"{method} {url} should return JSON"
    
    def test_error_responses_have_consistent_structure(self, client):
        """Verify all error responses follow same structure."""
        # Validation error
        response1 = client.post('/api/pomodoro/start', json={'duration_minutes': 0})
        data1 = response1.get_json()
        assert 'error' in data1
        
        # Another validation error
        response2 = client.post('/api/pomodoro/break', json={'duration_minutes': 500})
        data2 = response2.get_json()
        assert 'error' in data2
        
        # Conflict error
        client.post('/api/pomodoro/start', json={'duration_minutes': 25})
        response3 = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
        data3 = response3.get_json()
        assert 'error' in data3

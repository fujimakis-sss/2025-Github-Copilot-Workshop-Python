"""Tests for tag functionality."""
import pytest
from app import create_app
from pomodoro.models import db, PomodoroSession
from pomodoro.services import start_focus, start_break, get_stats_by_tag, get_recent_tags
from pomodoro.validators import ValidationError


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


@pytest.fixture
def app_context(app):
    with app.app_context():
        yield


def test_start_focus_with_tag(app_context):
    """Test starting focus session with a tag."""
    session = start_focus(25, "Project A")
    assert session.id is not None
    assert session.tag == "Project A"


def test_start_focus_without_tag(app_context):
    """Test starting focus session without a tag."""
    session = start_focus(25)
    assert session.id is not None
    assert session.tag is None


def test_start_break_with_tag(app_context):
    """Test starting break session with a tag."""
    session = start_break(5, "Coffee break")
    assert session.id is not None
    assert session.tag == "Coffee break"


def test_tag_validation_max_length(app_context):
    """Test that tag validation rejects tags longer than 50 characters."""
    long_tag = "A" * 51
    with pytest.raises(ValidationError, match="Tag must be at most 50 characters"):
        start_focus(25, long_tag)


def test_tag_validation_exactly_50_chars(app_context):
    """Test that tag validation accepts tags exactly 50 characters."""
    tag = "A" * 50
    session = start_focus(25, tag)
    assert session.id is not None
    assert session.tag == tag


def test_tag_in_session_dict(app_context):
    """Test that tag is included in session to_dict."""
    session = start_focus(25, "Test Tag")
    session_dict = session.to_dict()
    assert 'tag' in session_dict
    assert session_dict['tag'] == "Test Tag"


def test_stats_by_tag_no_sessions(app_context):
    """Test stats by tag with no sessions."""
    stats = get_stats_by_tag()
    assert stats == []


def test_stats_by_tag_with_completed_sessions(app_context):
    """Test stats by tag with completed sessions."""
    from pomodoro.services import complete_session
    
    # Create and complete sessions with different tags
    session1 = start_focus(25, "Project A")
    complete_session(session1.id)
    
    session2 = start_focus(30, "Project A")
    complete_session(session2.id)
    
    session3 = start_focus(15, "Project B")
    complete_session(session3.id)
    
    stats = get_stats_by_tag()
    
    # Should have 2 tag groups
    assert len(stats) == 2
    
    # Find Project A stats
    project_a = next((s for s in stats if s['tag'] == "Project A"), None)
    assert project_a is not None
    assert project_a['completed_focus_count'] == 2
    assert project_a['total_focus_seconds'] == (25 + 30) * 60
    
    # Find Project B stats
    project_b = next((s for s in stats if s['tag'] == "Project B"), None)
    assert project_b is not None
    assert project_b['completed_focus_count'] == 1
    assert project_b['total_focus_seconds'] == 15 * 60


def test_stats_by_tag_excludes_active_sessions(app_context):
    """Test that stats by tag excludes active sessions."""
    # Create an active session
    start_focus(25, "Active Tag")
    
    stats = get_stats_by_tag()
    assert stats == []


def test_stats_by_tag_excludes_break_sessions(app_context):
    """Test that stats by tag only includes focus sessions."""
    from pomodoro.services import complete_session
    
    # Create and complete a break session
    session = start_break(5, "Break Tag")
    complete_session(session.id)
    
    stats = get_stats_by_tag()
    assert stats == []


def test_recent_tags_no_sessions(app_context):
    """Test recent tags with no sessions."""
    tags = get_recent_tags()
    assert tags == []


def test_recent_tags_with_sessions(app_context):
    """Test recent tags returns unique tags ordered by recency."""
    # Create sessions with different tags
    start_focus(25, "Tag A")
    from pomodoro.services import stop_active_session
    stop_active_session()
    
    start_focus(25, "Tag B")
    stop_active_session()
    
    start_focus(25, "Tag A")  # Duplicate tag
    stop_active_session()
    
    start_focus(25, "Tag C")
    stop_active_session()
    
    tags = get_recent_tags()
    
    # Should return unique tags
    assert len(tags) == 3
    # Most recent should be Tag C
    assert tags[0] == "Tag C"
    # Tag A should appear once even though used twice
    assert tags.count("Tag A") == 1


def test_recent_tags_excludes_null(app_context):
    """Test that recent tags excludes sessions without tags."""
    # Create sessions with and without tags
    start_focus(25, "Tag A")
    from pomodoro.services import stop_active_session
    stop_active_session()
    
    start_focus(25)  # No tag
    stop_active_session()
    
    tags = get_recent_tags()
    assert len(tags) == 1
    assert tags[0] == "Tag A"


def test_recent_tags_limit(app_context):
    """Test that recent tags respects limit parameter."""
    from pomodoro.services import stop_active_session
    
    # Create 15 sessions with different tags
    for i in range(15):
        start_focus(1, f"Tag {i}")
        stop_active_session()
    
    tags = get_recent_tags(5)
    assert len(tags) == 5


def test_start_focus_route_with_tag(client):
    """Test /start endpoint accepts tag parameter."""
    response = client.post('/api/pomodoro/start', json={
        'duration_minutes': 25,
        'tag': 'API Test Tag'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data


def test_start_break_route_with_tag(client):
    """Test /break endpoint accepts tag parameter."""
    response = client.post('/api/pomodoro/break', json={
        'duration_minutes': 5,
        'tag': 'Break Tag'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data


def test_stats_by_tag_endpoint(client):
    """Test /stats/by-tag endpoint."""
    response = client.get('/api/pomodoro/stats/by-tag')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_recent_tags_endpoint(client):
    """Test /tags/recent endpoint."""
    response = client.get('/api/pomodoro/tags/recent')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_recent_tags_endpoint_with_limit(client):
    """Test /tags/recent endpoint with limit parameter."""
    response = client.get('/api/pomodoro/tags/recent?limit=5')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

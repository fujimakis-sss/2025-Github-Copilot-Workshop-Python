"""Tests for statistics endpoints."""
import pytest
from datetime import datetime, date, timedelta, timezone
from app import create_app
from pomodoro.models import db, DailyStat


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
def sample_stats(app):
    """Create sample daily stats for testing."""
    with app.app_context():
        today = date.today()
        # Create stats for the last 10 days
        for i in range(10):
            day = today - timedelta(days=i)
            stat = DailyStat(
                date=day,
                total_focus_seconds=(i + 1) * 1500,  # 25 minutes * (i+1)
                completed_focus_count=i + 1
            )
            db.session.add(stat)
        db.session.commit()
        yield


def test_weekly_stats_endpoint(client, sample_stats):
    """Test /stats/weekly endpoint returns 7 days of data."""
    response = client.get('/api/pomodoro/stats/weekly')
    assert response.status_code == 200
    
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 7
    
    # Check structure of each entry
    for entry in data:
        assert 'date' in entry
        assert 'focus_count' in entry
        assert 'total_seconds' in entry
        assert 'completion_rate' in entry


def test_monthly_stats_endpoint(client, sample_stats):
    """Test /stats/monthly endpoint returns 30 days of data."""
    response = client.get('/api/pomodoro/stats/monthly')
    assert response.status_code == 200
    
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 30
    
    # Check structure of each entry
    for entry in data:
        assert 'date' in entry
        assert 'focus_count' in entry
        assert 'total_seconds' in entry
        assert 'completion_rate' in entry


def test_weekly_stats_with_data(client, sample_stats):
    """Test weekly stats contains correct data."""
    response = client.get('/api/pomodoro/stats/weekly')
    data = response.get_json()
    
    # Most recent day should have data (today is index 0 in sample_stats)
    most_recent = data[-1]
    assert most_recent['focus_count'] > 0
    assert most_recent['total_seconds'] > 0
    assert most_recent['completion_rate'] > 0


def test_monthly_stats_with_data(client, sample_stats):
    """Test monthly stats contains correct data."""
    response = client.get('/api/pomodoro/stats/monthly')
    data = response.get_json()
    
    # Most recent day should have data
    most_recent = data[-1]
    assert most_recent['focus_count'] > 0
    assert most_recent['total_seconds'] > 0
    assert most_recent['completion_rate'] > 0


def test_weekly_stats_empty_database(client):
    """Test weekly stats with no data returns zeros."""
    response = client.get('/api/pomodoro/stats/weekly')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data) == 7
    
    # All entries should be zero
    for entry in data:
        assert entry['focus_count'] == 0
        assert entry['total_seconds'] == 0
        assert entry['completion_rate'] == 0.0


def test_monthly_stats_empty_database(client):
    """Test monthly stats with no data returns zeros."""
    response = client.get('/api/pomodoro/stats/monthly')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data) == 30
    
    # All entries should be zero
    for entry in data:
        assert entry['focus_count'] == 0
        assert entry['total_seconds'] == 0
        assert entry['completion_rate'] == 0.0


def test_weekly_stats_date_order(client, sample_stats):
    """Test weekly stats are in chronological order."""
    response = client.get('/api/pomodoro/stats/weekly')
    data = response.get_json()
    
    dates = [entry['date'] for entry in data]
    # Dates should be in ascending order
    assert dates == sorted(dates)


def test_monthly_stats_date_order(client, sample_stats):
    """Test monthly stats are in chronological order."""
    response = client.get('/api/pomodoro/stats/monthly')
    data = response.get_json()
    
    dates = [entry['date'] for entry in data]
    # Dates should be in ascending order
    assert dates == sorted(dates)

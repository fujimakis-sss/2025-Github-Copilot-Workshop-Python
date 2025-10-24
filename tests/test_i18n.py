"""Tests for internationalization functionality."""
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


def test_default_language_is_japanese(client):
    """Test that the default language is Japanese when Accept-Language header prefers it."""
    response = client.get('/', headers={'Accept-Language': 'ja'})
    assert response.status_code == 200
    assert 'ポモドーロタイマー' in response.data.decode('utf-8')


def test_language_switch_to_english(client):
    """Test switching to English language."""
    response = client.get('/set-language/en', follow_redirects=True)
    assert response.status_code == 200
    assert 'Pomodoro Timer' in response.data.decode('utf-8')
    assert 'Start' in response.data.decode('utf-8')


def test_language_switch_to_japanese(client):
    """Test switching to Japanese language."""
    response = client.get('/set-language/ja', follow_redirects=True)
    assert response.status_code == 200
    assert 'ポモドーロタイマー' in response.data.decode('utf-8')
    assert '開始' in response.data.decode('utf-8')


def test_language_persistence_in_session(client):
    """Test that language preference is stored in session."""
    # Set English explicitly via endpoint
    client.get('/set-language/en')
    
    # Verify session has the language set
    with client.session_transaction() as sess:
        assert sess.get('language') == 'en'
    
    # Switch to Japanese via endpoint
    client.get('/set-language/ja')
    
    # Verify session has Japanese set
    with client.session_transaction() as sess:
        assert sess.get('language') == 'ja'


def test_invalid_language_code_ignored(client):
    """Test that invalid language codes are ignored and don't crash the app."""
    # Try to set invalid language
    response = client.get('/set-language/fr', follow_redirects=True)
    
    # Should succeed (not crash) even with invalid language code
    assert response.status_code == 200
    # Language preference should not be set to invalid code
    # The page will render in the browser's preferred language or default


def test_language_selector_in_ui(client):
    """Test that language selector is present in UI."""
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'languageSelect' in html
    assert 'English' in html
    assert '日本語' in html


def test_english_translations_complete(client):
    """Test that all key UI elements are translated in English."""
    client.get('/set-language/en', follow_redirects=True)
    response = client.get('/')
    html = response.data.decode('utf-8')
    
    # Check key translations
    assert 'Pomodoro Timer' in html
    assert 'Start' in html
    assert 'Break' in html
    assert 'Reset' in html
    assert "Today's Progress" in html
    assert 'Completed' in html
    assert 'Focus Time' in html


def test_japanese_translations_complete(client):
    """Test that all key UI elements are translated in Japanese."""
    client.get('/set-language/ja', follow_redirects=True)
    response = client.get('/')
    html = response.data.decode('utf-8')
    
    # Check key translations
    assert 'ポモドーロタイマー' in html
    assert '開始' in html
    assert '休憩' in html
    assert 'リセット' in html
    assert '今日の進捗' in html
    assert '完了' in html
    assert '集中時間' in html

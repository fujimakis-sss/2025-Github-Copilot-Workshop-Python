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


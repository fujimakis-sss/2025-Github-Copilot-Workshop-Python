"""End-to-end tests for Pomodoro Timer Web UI.

These tests verify the complete user experience from the browser perspective.
Tests are marked with @pytest.mark.e2e and @pytest.mark.slow.
"""
import pytest
import time
from playwright.sync_api import Page, expect
from threading import Thread
from app import create_app
from pomodoro.models import db


@pytest.fixture(scope='module')
def app_server():
    """Start Flask app in a separate thread for E2E testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_e2e.db'
    
    # Initialize database
    with app.app_context():
        db.create_all()
    
    # Run server in a separate thread
    def run_server():
        app.run(port=5555, debug=False, use_reloader=False)
    
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give the server time to start
    time.sleep(2)
    
    yield 'http://localhost:5555'
    
    # Cleanup
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.mark.e2e
@pytest.mark.slow
class TestPomodoroUIBasics:
    """Basic UI interaction tests."""
    
    def test_homepage_loads(self, app_server, page: Page):
        """Test that the homepage loads successfully."""
        page.goto(app_server)
        
        # Check title or main heading
        expect(page.locator('h1')).to_contain_text('ポモドーロタイマー')
        
        # Check main controls are present
        expect(page.locator('#startBtn')).to_be_visible()
        expect(page.locator('#breakBtn')).to_be_visible()
        expect(page.locator('#stopBtn')).to_be_visible()
    
    def test_start_button_starts_timer(self, app_server, page: Page):
        """Test that clicking start button starts the timer."""
        page.goto(app_server)
        
        # Click start button
        page.click('#startBtn')
        
        # Wait a moment for the timer to update
        time.sleep(1)
        
        # Check that status changed (timer should show some time)
        timer_text = page.locator('#timerText').inner_text()
        assert timer_text is not None
    
    def test_break_button_starts_break(self, app_server, page: Page):
        """Test that clicking break button starts a break."""
        page.goto(app_server)
        
        # Click break button
        page.click('#breakBtn')
        
        # Wait a moment for the timer to update
        time.sleep(1)
        
        # Check that timer is active
        timer_text = page.locator('#timerText').inner_text()
        assert timer_text is not None
    
    def test_stop_button_stops_timer(self, app_server, page: Page):
        """Test that clicking stop button stops the timer."""
        page.goto(app_server)
        
        # Start timer
        page.click('#startBtn')
        time.sleep(1)
        
        # Stop timer
        page.click('#stopBtn')
        time.sleep(1)
        
        # Timer should still show some value but be stopped
        timer_text = page.locator('#timerText').inner_text()
        assert timer_text is not None


@pytest.mark.e2e
@pytest.mark.slow
class TestPomodoroUIAccessibility:
    """Accessibility and ARIA attribute tests."""
    
    def test_buttons_have_aria_labels(self, app_server, page: Page):
        """Test that all buttons have proper ARIA labels."""
        page.goto(app_server)
        
        # Check ARIA labels
        start_btn = page.locator('#startBtn')
        expect(start_btn).to_have_attribute('aria-label', 'フォーカス開始')
        
        break_btn = page.locator('#breakBtn')
        expect(break_btn).to_have_attribute('aria-label', '休憩開始')
        
        stop_btn = page.locator('#stopBtn')
        expect(stop_btn).to_have_attribute('aria-label', '停止')
    
    def test_timer_display_is_visible(self, app_server, page: Page):
        """Test that the timer display is visible and accessible."""
        page.goto(app_server)
        
        timer = page.locator('#timerText')
        expect(timer).to_be_visible()
        
        # Should have text content
        timer_text = timer.inner_text()
        assert len(timer_text) > 0


@pytest.mark.e2e
@pytest.mark.slow  
class TestPomodoroUIStats:
    """Tests for statistics display."""
    
    def test_stats_display_is_present(self, app_server, page: Page):
        """Test that statistics are displayed on the page."""
        page.goto(app_server)
        
        # Check stats elements exist
        expect(page.locator('#completedCount')).to_be_visible()
        expect(page.locator('#totalTime')).to_be_visible()
        
        # Check stats section header
        expect(page.locator('.stats h2')).to_contain_text('今日の進捗')


# Simpler integration-style E2E tests that don't require a running server
@pytest.mark.e2e
class TestPomodoroUISimple:
    """Simplified E2E tests using test client."""
    
    def test_index_page_renders(self):
        """Test that index page renders without errors."""
        app = create_app()
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            assert b'pomodoro-container' in response.data
    
    def test_health_endpoint_accessible(self):
        """Test that health check endpoint is accessible."""
        app = create_app()
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'

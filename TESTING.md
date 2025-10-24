# Testing Documentation

## Overview

This document describes the test suite for the Pomodoro Timer Web Application. The test suite includes unit tests, integration tests, API contract tests, and end-to-end (E2E) tests.

## Test Statistics

- **Total Tests**: 76+ tests
- **Code Coverage**: 95%
- **Test Files**: 5 files
  - `test_validators.py` - 10 tests
  - `test_services.py` - 23 tests
  - `test_routes.py` - 26 tests
  - `test_api_contract.py` - 13 tests
  - `test_e2e.py` - 2+ tests

## Test Categories

### Unit Tests

**File**: `test_validators.py`
- Tests for validation functions
- Boundary value testing
- Type validation
- Error handling

**File**: `test_services.py` (partial)
- Service layer business logic tests
- Session management tests
- State calculation tests
- Statistics tracking tests

### Integration Tests

**File**: `test_routes.py`
- API endpoint integration tests
- Request/response validation
- Error handling
- Edge cases and conflict scenarios
- JSON body handling

**File**: `test_services.py` (partial)
- Database integration tests
- Session lifecycle tests
- Multi-session scenarios

### API Contract Tests

**File**: `test_api_contract.py`
- Response schema validation
- HTTP status code verification
- Content-Type validation
- ISO 8601 datetime format validation
- API consistency checks

Tested endpoints:
- `POST /api/pomodoro/start`
- `POST /api/pomodoro/break`
- `POST /api/pomodoro/stop`
- `GET /api/pomodoro/state`
- `GET /health`

### End-to-End Tests

**File**: `test_e2e.py`
- UI rendering tests
- Page accessibility tests
- Health check validation

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_routes.py
pytest tests/test_services.py
pytest tests/test_validators.py
pytest tests/test_api_contract.py
pytest tests/test_e2e.py
```

### Run with Coverage

```bash
pytest --cov=pomodoro --cov=app --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Run with Coverage Report in Terminal

```bash
pytest --cov=pomodoro --cov=app --cov-report=term-missing
```

### Run Tests by Marker

```bash
# Run only E2E tests
pytest -m e2e

# Run only integration tests
pytest -m integration

# Run only contract tests
pytest -m contract

# Skip slow tests
pytest -m "not slow"
```

### Run Specific Test Class or Function

```bash
# Run specific test class
pytest tests/test_api_contract.py::TestStartFocusContract

# Run specific test function
pytest tests/test_routes.py::test_start_focus_valid_duration
```

### Verbose Output

```bash
pytest -v
```

### Show Print Statements

```bash
pytest -s
```

## Test Coverage

Current coverage: **95%**

Coverage breakdown by module:
- `pomodoro/routes.py`: 100%
- `pomodoro/services.py`: 100%
- `pomodoro/validators.py`: 100%
- `pomodoro/__init__.py`: 100%
- `pomodoro/models.py`: 91%
- `app.py`: 74%

To improve coverage:
- Add tests for `app.py` blueprint registration error handling
- Add tests for model `to_dict()` methods
- Add more E2E tests for UI interactions

## Test Configuration

Test configuration is in `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    contract: API contract tests
    e2e: End-to-end tests
    slow: Tests that take a long time to run
```

## Continuous Integration

### GitHub Actions

To run tests in CI, add a workflow file `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=pomodoro --cov=app --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Writing New Tests

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Unit Test

```python
def test_validate_duration_valid():
    """Test that validation accepts valid duration."""
    validate_duration(25)  # Should not raise
```

### Example Integration Test

```python
def test_start_focus_valid_duration(client):
    """Test /start endpoint accepts valid duration."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
```

### Example Contract Test

```python
def test_success_response_structure(client):
    """Verify success response contains required fields."""
    response = client.post('/api/pomodoro/start', json={'duration_minutes': 25})
    data = response.get_json()
    assert 'id' in data
    assert 'type' in data
    assert isinstance(data['id'], int)
```

## Fixtures

Common fixtures available in tests:

- `app`: Flask application instance with test config
- `client`: Flask test client for making requests
- `app_context`: Application context for database operations

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures to clean up after tests
3. **Descriptive Names**: Test names should describe what they test
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Edge Cases**: Test boundary values and error conditions
6. **Documentation**: Add docstrings to describe test purpose

## Troubleshooting

### Tests Failing Due to Database

If tests fail with database errors, ensure:
- Database is properly cleaned up between tests
- Fixtures are correctly scoped
- In-memory SQLite is used for tests

### Import Errors

If you get import errors:
- Ensure virtual environment is activated
- Install all dependencies: `pip install -r requirements.txt`
- Check PYTHONPATH includes project root

### Coverage Not Matching Expected

Run with `--cov-report=term-missing` to see which lines are not covered:
```bash
pytest --cov=pomodoro --cov-report=term-missing
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Flask testing documentation](https://flask.palletsprojects.com/en/latest/testing/)
- [Playwright documentation](https://playwright.dev/python/)

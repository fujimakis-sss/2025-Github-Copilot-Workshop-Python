"""Tests for validation functions."""
import pytest
from pomodoro.validators import validate_duration, ValidationError


def test_validate_duration_valid_min_boundary():
    """Test validation accepts minimum valid duration (1 minute)."""
    validate_duration(1)  # Should not raise


def test_validate_duration_valid_max_boundary():
    """Test validation accepts maximum valid duration (240 minutes)."""
    validate_duration(240)  # Should not raise


def test_validate_duration_valid_middle():
    """Test validation accepts typical duration values."""
    validate_duration(25)  # Should not raise
    validate_duration(5)   # Should not raise
    validate_duration(50)  # Should not raise


def test_validate_duration_too_low():
    """Test validation rejects duration below minimum."""
    with pytest.raises(ValidationError, match="Duration must be at least 1 minute"):
        validate_duration(0)


def test_validate_duration_negative():
    """Test validation rejects negative duration."""
    with pytest.raises(ValidationError, match="Duration must be at least 1 minute"):
        validate_duration(-1)


def test_validate_duration_too_high():
    """Test validation rejects duration above maximum."""
    with pytest.raises(ValidationError, match="Duration must be at most 240 minutes"):
        validate_duration(241)


def test_validate_duration_way_too_high():
    """Test validation rejects extremely high duration."""
    with pytest.raises(ValidationError, match="Duration must be at most 240 minutes"):
        validate_duration(1000)


def test_validate_duration_invalid_type_string():
    """Test validation rejects string input."""
    with pytest.raises(ValidationError, match="Duration must be a number"):
        validate_duration("25")


def test_validate_duration_invalid_type_none():
    """Test validation rejects None input."""
    with pytest.raises(ValidationError, match="Duration must be a number"):
        validate_duration(None)


def test_validate_duration_float():
    """Test validation accepts float values within range."""
    validate_duration(25.5)  # Should not raise

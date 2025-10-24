"""Validation functions for Pomodoro API."""

MIN_DURATION_MINUTES = 1
MAX_DURATION_MINUTES = 240


class ValidationError(ValueError):
    """Exception raised for validation errors."""
    pass


def validate_duration(duration_minutes: int) -> None:
    """
    Validate that duration is within acceptable range.
    
    Args:
        duration_minutes: Duration in minutes to validate
        
    Raises:
        ValidationError: If duration is outside the valid range (1-240 minutes)
    """
    if not isinstance(duration_minutes, (int, float)):
        raise ValidationError("Duration must be a number")
    
    if duration_minutes < MIN_DURATION_MINUTES:
        raise ValidationError(f"Duration must be at least {MIN_DURATION_MINUTES} minute(s)")
    
    if duration_minutes > MAX_DURATION_MINUTES:
        raise ValidationError(f"Duration must be at most {MAX_DURATION_MINUTES} minutes")

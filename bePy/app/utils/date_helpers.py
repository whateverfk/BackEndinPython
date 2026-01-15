"""
Date conversion utilities

Centralizes date handling logic to eliminate code duplication.
Consolidates: app/features/deps.py::to_date and 
              app/features/background/update_data_record.py::normalize_to_date
"""
from datetime import datetime, date
from typing import Optional


def to_date(value) -> Optional[date]:
    """
    Convert various date formats to datetime.date
    
    Args:
        value: Can be date, datetime, string (YYYY-MM-DD), or None
    
    Returns:
        date object or None
        
    Raises:
        TypeError: If value type is not supported
        ValueError: If string format is invalid
    
    Examples:
        >>> to_date("2025-01-15")
        date(2025, 1, 15)
        >>> to_date(datetime(2025, 1, 15, 10, 30))
        date(2025, 1, 15)
        >>> to_date(None)
        None
    """
    if value is None:
        return None
    
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    
    if isinstance(value, datetime):
        return value.date()
    
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    
    raise TypeError(f"Invalid date type: {type(value)}")


def to_date_str(value) -> Optional[str]:
    """
    Convert date value to YYYY-MM-DD string format
    
    Args:
        value: Any value that to_date() can handle
    
    Returns:
        Date string in YYYY-MM-DD format, or None
    
    Examples:
        >>> to_date_str(date(2025, 1, 15))
        "2025-01-15"
        >>> to_date_str(None)
        None
    """
    d = to_date(value)
    return d.strftime("%Y-%m-%d") if d else None

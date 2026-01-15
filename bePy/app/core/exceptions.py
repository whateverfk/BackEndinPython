"""
Custom exception classes

Provides consistent error handling patterns across the application.
These wrap HTTPException to provide clearer semantics without changing
the actual HTTP responses.
"""
from fastapi import HTTPException, status


class DeviceNotFoundError(HTTPException):
    """Raised when a device cannot be found in the database"""
    
    def __init__(self, message: str = "Device not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class ChannelNotFoundError(HTTPException):
    """Raised when a channel cannot be found in the database"""
    
    def __init__(self, message: str = "Channel not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class UserNotFoundError(HTTPException):
    """Raised when a user cannot be found in the database"""
    
    def __init__(self, message: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class DeviceConnectionError(HTTPException):
    """Raised when cannot connect to a device"""
    
    def __init__(self, message: str = "Cannot connect to device"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=message
        )


class AuthenticationError(HTTPException):
    """Raised for authentication failures"""
    
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )


class InvalidDateFormatError(HTTPException):
    """Raised when date format is invalid"""
    
    def __init__(self, message: str = "Invalid date format. Use YYYY-MM"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

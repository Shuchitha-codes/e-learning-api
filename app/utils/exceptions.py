
from fastapi import HTTPException, status
from typing import Optional

class AuthException(HTTPException):
    """Custom authentication exception"""
    def __init__(self, detail: str = "Authentication failed", status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)


class PermissionException(HTTPException):
    """Custom permission exception"""
    def __init__(self, detail: str = "Insufficient permissions", status_code: int = status.HTTP_403_FORBIDDEN):
        super().__init__(status_code=status_code, detail=detail)


class ValidationException(HTTPException):
    """Custom validation exception"""
    def __init__(self, detail: str = "Validation error", status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY):
        super().__init__(status_code=status_code, detail=detail)


class DatabaseException(HTTPException):
    """Custom database exception"""
    def __init__(self, detail: str = "Database operation failed", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)
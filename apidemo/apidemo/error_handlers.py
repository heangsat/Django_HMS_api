"""
Error handling and exception utilities for the API.
Provides consistent error responses across all endpoints.
"""
from django.http import JsonResponse
import traceback
import logging

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base exception class for API errors."""
    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "UNKNOWN_ERROR"
        super().__init__(self.message)


class NotFoundError(APIException):
    """Raised when a resource is not found."""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f" (ID: {identifier})"
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class ValidationError(APIException):
    """Raised when input validation fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400, error_code="VALIDATION_ERROR")


class DatabaseError(APIException):
    """Raised when database operation fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_code="DATABASE_ERROR")


class UnauthorizedError(APIException):
    """Raised when user is not authenticated."""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED")


def format_error_response(exc: Exception, request=None):
    """
    Format exception into a structured error response.
    
    Args:
        exc: Exception instance
        request: Django request object (optional)
        
    Returns:
        Dict with error details
    """
    if isinstance(exc, APIException):
        return {
            "error": True,
            "code": exc.error_code,
            "message": exc.message,
            "status": exc.status_code,
        }
    else:
        # Log unexpected errors
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return {
            "error": True,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "status": 500,
        }


def create_success_response(data, message: str = None, status: int = 200):
    """Create a consistent success response."""
    response = {
        "error": False,
        "status": status,
        "data": data,
    }
    if message:
        response["message"] = message
    return response


def create_error_response(error: str, code: str = "ERROR", status: int = 400):
    """Create a consistent error response."""
    return {
        "error": True,
        "status": status,
        "code": code,
        "message": error,
    }


def safe_operation(operation_func, error_message: str = "Operation failed"):
    """
    Safely execute an operation with error handling.
    
    Args:
        operation_func: Callable that performs the operation
        error_message: Message to use if operation fails
        
    Returns:
        Result of operation_func or APIException on failure
    """
    try:
        return operation_func()
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}", exc_info=True)
        if isinstance(e, APIException):
            raise
        raise DatabaseError(error_message)

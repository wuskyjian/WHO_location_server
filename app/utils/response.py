from typing import Any, Optional
from flask import jsonify, make_response


class AuthError(Exception):
    """Authentication/Authorization error."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


class NotFoundError(Exception):
    """Exception raised for resource not found errors."""
    def __init__(self, message, error=None, status_code=404):
        self.message = message
        self.error = error
        self.status_code = status_code


def success_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    status_code: int = 200
) -> tuple:
    """Create a success response."""
    response = {}
    if message:
        response["message"] = message
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code


def redirect_response(
    status_code: int = 304,
    location: Optional[str] = None
) -> tuple:
    """Create a redirect response without body."""
    if not (300 <= status_code <= 399):
        raise ValueError("Status code must be 3XX")
        
    if status_code != 304 and not location:
        raise ValueError("Location is required for non-304 redirects")
        
    response = make_response('', status_code)
    if location:
        response.headers['Location'] = location
        
    return response


def error_response(
    message: str,
    error: Optional[str] = None,
    status_code: int = 400
) -> tuple:
    """Create an error response."""
    response = {"message": message}
    if error:
        response["error"] = error
    return jsonify(response), status_code 
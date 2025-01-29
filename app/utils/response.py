from typing import Any, Optional
from flask import jsonify


class AuthError(Exception):
    """Authentication/Authorization error."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
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
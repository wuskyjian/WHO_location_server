from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from app.utils.response import AuthError
from app.services.user_service import UserService

def handle_api_error(f):
    """Decorator for handling API endpoint errors.
    
    This decorator provides consistent error handling for all API endpoints:
    - Logs all errors
    - Returns standardized error responses
    - Handles both AuthError and general exceptions
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AuthError as e:
            # Handle authentication/authorization errors
            current_app.logger.warning(
                f"Auth error in {f.__name__}: {str(e)}",
                extra={'endpoint': f.__name__, 'error_type': 'auth'}
            )
            return jsonify({"message": e.message}), e.status_code
        except Exception as e:
            # Handle all other errors
            current_app.logger.error(
                f"Error in {f.__name__}: {str(e)}",
                extra={'endpoint': f.__name__, 'error_type': 'general'},
                exc_info=True
            )
            return jsonify({
                "message": "Internal server error",
                "error": str(e) if current_app.debug else None
            }), 500
            
    return decorated_function 

def admin_required(f):
    """Decorator to check if the current user is an admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        current_user = UserService.get_by_id(current_user_id)
        
        if not current_user or current_user.role != 'admin':
            return jsonify({"message": "Access forbidden: Admins only"}), 403
            
        return f(*args, **kwargs)
    return decorated_function 
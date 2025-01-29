from app.utils.response import AuthError

class RequestValidator:
    """Validator for request data."""
    
    ALLOWED_ROLES = {'ambulance', 'cleaning_team', 'admin'}
    MIN_USERNAME_LENGTH = 3
    PASSWORD_LENGTH = 8
    
    @classmethod
    def validate_register_data(cls, data):
        if not data:
            raise AuthError("No data provided")
            
        if not all(field in data for field in ['username', 'password', 'role']):
            raise AuthError("Missing required fields")
            
        if data['role'] not in cls.ALLOWED_ROLES:
            raise AuthError(f"Invalid role. Allowed roles are: {', '.join(cls.ALLOWED_ROLES)}")
            
        if not isinstance(data['username'], str) or len(data['username']) < cls.MIN_USERNAME_LENGTH:
            raise AuthError(f"Username must be at least {cls.MIN_USERNAME_LENGTH} characters long")
            
        if not isinstance(data['password'], str) or len(data['password']) < cls.PASSWORD_LENGTH:
            raise AuthError(f"Password must be at least {cls.PASSWORD_LENGTH} long") 
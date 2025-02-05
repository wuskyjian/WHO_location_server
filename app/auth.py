from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, decode_token
from app.utils.response import AuthError, error_response, success_response
from app.utils.validators import RequestValidator
from app.utils.decorators import admin_required
from app.services.user_service import UserService

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.errorhandler(AuthError)
def handle_auth_error(error):
    """Global error handler for AuthError exceptions."""
    return error_response(message=error.message, status_code=error.status_code)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    if not request.is_json:
        raise AuthError("Missing JSON in request", 400)
        
    data = request.get_json()
    RequestValidator.validate_register_data(data)
    
    user = UserService.create_user(
        username=data['username'],
        password=data['password'],
        role=data['role']
    )
    
    access_token = create_access_token(identity=str(user.id))
    
    return success_response(
        data={
            "token": access_token,
            "token_type": "Bearer",
            "expires_in": int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()),
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            }
        },
        message="User registered successfully",
        status_code=201
    )

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint."""
    if not request.is_json:
        raise AuthError("Missing JSON in request", 400)

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        raise AuthError("Missing username or password", 400)

    user = UserService.get_by_username(username)
    if user is None or not user.check_password(password):
        raise AuthError("Invalid username or password", 401)

    access_token = create_access_token(identity=str(user.id), additional_claims={"sub": str(user.id)})
    
    # Decode the JWT token manually
    decoded_token = decode_token(access_token)
    print("\n" + "=" * 50)
    print("【Login】")
    print(f"Decoded token: {decoded_token}")
    print("\n" + "=" * 50)

    return success_response(
        data={
            "token": access_token,
            "token_type": "Bearer",
            "expires_in": int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()),
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            }
        },
        message="Login successful"
    )

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def list_users():
    """Get users by role."""
    role = request.args.get('role')
    if role:
        users = UserService.get_users_by_role(role)
    else:
        users = UserService.get_non_admin_users()
        
    return success_response(
        data=[user.to_dict() for user in users],
        message=f"Retrieved {len(users)} users"
    )

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """Delete a user by ID."""
    UserService.delete_user(
        user_id=user_id,
        admin_id=int(get_jwt_identity())
    )
    
    return success_response(
        data={"deleted_id": user_id},
        message=f"User {user_id} deleted successfully"
    )

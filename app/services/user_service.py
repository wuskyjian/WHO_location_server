from app import db
from app.models import User
from app.utils.response import AuthError

class UserService:
    """Service class for user-related operations."""
    
    @staticmethod
    def get_by_id(user_id):
        return db.session.get(User, user_id)
    
    @staticmethod
    def get_by_username(username):
        return db.session.query(User).filter_by(username=username).first()
    
    @staticmethod
    def get_users_by_role(role):
        return db.session.query(User).filter_by(role=role).all()
    
    @staticmethod
    def get_non_admin_users():
        return db.session.query(User).filter(User.role != 'admin').all()
    
    @classmethod
    def create_user(cls, username, password, role):
        if cls.get_by_username(username):
            raise AuthError("Username already exists")
            
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    
    @classmethod
    def delete_user(cls, user_id, admin_id):
        user = cls.get_by_id(user_id)
        if not user:
            raise AuthError("User not found", 404)
        
        if user.id == admin_id:
            raise AuthError("Admins cannot delete themselves")
            
        db.session.delete(user)
        db.session.commit() 
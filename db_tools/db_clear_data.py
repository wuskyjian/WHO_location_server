import os
import sys
# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Task, TaskLog, GlobalCounter   

def clear_all_data():
    """Clear all data from the database."""
    # Delete records in dependency order (child tables first)
    db.session.query(TaskLog).delete()
    db.session.query(Task).delete()
    db.session.query(User).delete()
    db.session.commit()
    GlobalCounter.reset_counter()
    print("🗑️  All data cleared successfully!")

if __name__ == "__main__":
    # Create the Flask application instance
    app = create_app()
    
    with app.app_context():
        try:
            clear_all_data()
        except Exception as e:
            print(f"❌ Error clearing data: {str(e)}")
            raise
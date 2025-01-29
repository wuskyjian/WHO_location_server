import os
import sys
import hashlib 

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Task, TaskLog
from db_tools.db_clear_data import clear_all_data
import random
import math

def generate_test_data():
    """Generate test data with valid business rules."""
    
    def create_user(username: str, role: str) -> User:
        """Create a user with a default password."""
        password = "password123"
        user = User(username=username, role=role)
        user.set_password(password)  
        db.session.add(user)
        return user

    def create_task(title: str, description: str, created_by: int, assigned_to: int, 
                   location_lat: float, location_lon: float, status: str = "new") -> Task:
        """Create a task with validation for role-based permissions."""
        # Validate creator-assignee relationships
        creator = db.session.get(User, created_by)
        assignee = db.session.get(User, assigned_to)

        role_validation = {
            "new": (
                ("admin", "ambulance"),
                ("ambulance", "ambulance")
            ),
            "in_progress": (
                ("admin", "cleaning_team"),
                ("ambulance", "cleaning_team")
            ),
            "completed": (
                ("admin", "cleaning_team"),
                ("ambulance", "cleaning_team")
            ),
            "issue_reported": (
                ("admin", "cleaning_team"),
                ("ambulance", "cleaning_team")
            )
        }

        if (creator.role, assignee.role) not in role_validation[status]:
            raise ValueError(f"Invalid {creator.role}→{assignee.role} assignment for status '{status}'")

        return Task(
            title=title,
            description=description,
            created_by=created_by,
            assigned_to=assigned_to,
            location_lat=location_lat,
            location_lon=location_lon,
            status=status
        )

    def create_task_log(task_id: int, status: str, assigned_to: int, 
                       modified_by: int, note: str) -> TaskLog:
        """Create a task log entry."""
        return TaskLog(
            task_id=task_id,
            status=status,
            assigned_to=assigned_to,
            modified_by=modified_by,
            note=note
        )

    # Initialize users
    users = [create_user("admin", "admin")]
    users += [create_user(f"ambulance_{i}", "ambulance") for i in range(1, 6)]
    users += [create_user(f"cleaning_team_{i}", "cleaning_team") for i in range(1, 6)]
    db.session.commit()

    # Generate tasks around Milan
    milan_lat, milan_lon = 45.4642, 9.1900  # Milan city center coordinates
    tasks = []
    
    for task_num in range(1, 11):  # Generate 10 tasks
        while True:
            try:
                # Randomly select creator and status
                creator = random.choice([u for u in users if u.role in ("admin", "ambulance")])
                status = random.choice(["new", "in_progress", "completed", "issue_reported"])
                
                # Determine assignee based on status
                target_role = "ambulance" if status == "new" else "cleaning_team"
                assignee = random.choice([u for u in users if u.role == target_role])
                
                # Generate geo-coordinates within 15 km of Milan
                angle = random.uniform(0, 2 * math.pi)  # Random angle in radians
                distance_km = random.uniform(0, 15)  # Random distance within 15 km
                lat_offset = (distance_km / 111) * math.cos(angle)  # Convert km to degrees
                lon_offset = (distance_km / 111) * math.sin(angle) / math.cos(math.radians(milan_lat))
                
                # Create task
                task = create_task(
                    title=f"Task {task_num}",
                    description=f"Description for Task {task_num}",
                    created_by=creator.id,
                    assigned_to=assignee.id,
                    location_lat=milan_lat + lat_offset,
                    location_lon=milan_lon + lon_offset,
                    status=status
                )
                db.session.add(task)
                db.session.flush()  # Generate task ID

                # Generate chronological logs
                status_flow = {
                    "new": ["new"],
                    "in_progress": ["new", "in_progress"],
                    "completed": ["new", "in_progress", "completed"],
                    "issue_reported": ["new", "in_progress", "issue_reported"]
                }[status]
                
                for idx, log_status in enumerate(status_flow):
                    log = TaskLog(
                        task_id=task.id,
                        status=log_status,
                        assigned_to=assignee.id,
                        modified_by=creator.id if idx == 0 else assignee.id,
                        note=f"Status progression: {log_status}"
                    )
                    db.session.add(log)

                tasks.append(task)
                db.session.commit()  # Commit task and logs
                break
                
            except ValueError as e:
                print(f"Skipping invalid task configuration: {e}")
                continue


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        clear_all_data()
        print("[1/2] Database cleared successfully")
        
        generate_test_data()
        print("[2/2] Test data generated successfully")
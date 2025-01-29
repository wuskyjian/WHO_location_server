import pytest
from app import db
from app.models import Task

@pytest.fixture
def add_task(app):
    """Add a test task to the database."""
    def _add_task(
        created_by,
        status="new",
        assigned_to=None,
        title="Default Task Title",
        location_lat=0.0,
        location_lon=0.0
    ):
        task = Task(
            title=title,
            description="Sample description",
            created_by=created_by,
            status=status,
            assigned_to=assigned_to,
            location_lat=location_lat,
            location_lon=location_lon
        )
        db.session.add(task)
        db.session.commit()
        return task
    return _add_task
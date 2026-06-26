import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import ORMCourse

# Setup test database (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestLearningHub(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)
        
        # Seed test data
        db = TestingSessionLocal()
        db.add(ORMCourse(
            title="Test Course",
            description="Test Description",
            main_link="http://test.com",
            status="Planning"
        ))
        db.commit()
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Learning Hub API is running. Use the main dashboard to access the Kanban board."})

    def test_get_courses(self):
        response = self.client.get("/api/courses")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Test Course")

    def test_create_course(self):
        course_data = {
            "title": "New Course",
            "description": "New Desc",
            "main_link": "http://new.com",
            "status": "WIP"
        }
        response = self.client.post("/api/courses", json=course_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "New Course")
        self.assertIn("id", data)

    def test_update_course(self):
        update_data = {
            "title": "Updated Course",
            "description": "Updated Desc",
            "main_link": "http://test.com",
            "status": "Archive"
        }
        response = self.client.put("/api/courses/1", json=update_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Updated Course")
        self.assertEqual(data["status"], "Archive")

    def test_delete_course(self):
        response = self.client.delete("/api/courses/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Course deleted"})
        
        # Verify it's gone
        get_response = self.client.get("/api/courses")
        self.assertEqual(len(get_response.json()), 0)

    def test_system_stats(self):
        response = self.client.get("/api/system-stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("cpu", data)
        self.assertIn("ram_percent", data)

    def test_bookmarks(self):
        response = self.client.get("/api/bookmarks")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Developer", data)

if __name__ == "__main__":
    unittest.main()

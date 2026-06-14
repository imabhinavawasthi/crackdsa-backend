from fastapi.testclient import TestClient
from app.main import app
from app.services.course_service import CourseService

app.dependency_overrides = {}

# Mock dependency
from app.api.deps import verify_admin_token
app.dependency_overrides[verify_admin_token] = lambda: {"id": "test_admin", "roles": ["admin"]}

client = TestClient(app)
response = client.get("/api/v1/admin/courses/")
print("Status:", response.status_code)
print("Response:", response.text)

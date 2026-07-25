from unittest.mock import MagicMock

import pytest

from app.api.deps import get_current_user, get_db
from app.main import app


@pytest.mark.asyncio
async def test_create_session_admin(client):
    """Verify that an admin can create sessions for any teacher and student."""
    mock_admin = MagicMock()
    mock_admin.id = 1
    mock_admin.role = "admin"

    mock_teacher = MagicMock()
    mock_teacher.id = 2
    mock_teacher.role = "teacher"
    mock_teacher.email = "teacher@example.com"
    mock_teacher.name = "Teacher Name"

    mock_student = MagicMock()
    mock_student.id = 3
    mock_student.role = "student"
    mock_student.email = "student@example.com"
    mock_student.name = "Student Name"

    mock_session = MagicMock()
    mock_session.id = 10
    mock_session.title = "Geometry Session"
    mock_session.description = "Introduction to angles"
    mock_session.date = "2026-07-27T10:00:00Z"
    mock_session.teacher_id = 2
    mock_session.student_id = 3
    mock_session.teacher = mock_teacher
    mock_session.student = mock_student

    # We mock execute to return a result that yields these side effects
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.side_effect = [
        mock_teacher,
        mock_student,
        mock_session,
    ]

    async def mock_execute(*args, **kwargs):
        return mock_result

    mock_db = MagicMock()
    mock_db.execute = mock_execute
    mock_db.add = MagicMock()

    async def mock_commit():
        pass

    async def mock_refresh(instance):
        pass

    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh

    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_db] = lambda: mock_db

    session_data = {
        "title": "Geometry Session",
        "description": "Introduction to angles",
        "date": "2026-07-27T10:00:00Z",
        "teacher_id": 2,
        "student_id": 3,
    }

    headers = {"Authorization": "Bearer mock-token"}
    response = await client.post("/api/v1/sessions/", json=session_data, headers=headers)
    assert response.status_code == 201
    assert response.json()["title"] == "Geometry Session"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_teacher_cannot_create_session_for_others(client):
    """Verify that a teacher role is restricted to scheduling sessions for themselves only."""
    mock_teacher = MagicMock()
    mock_teacher.id = 2
    mock_teacher.role = "teacher"

    app.dependency_overrides[get_current_user] = lambda: mock_teacher

    session_data = {
        "title": "Biology session",
        "description": "Cell structure",
        "date": "2026-07-27T10:00:00Z",
        "teacher_id": 99,
        "student_id": 3,
    }

    headers = {"Authorization": "Bearer mock-token"}
    response = await client.post("/api/v1/sessions/", json=session_data, headers=headers)
    assert response.status_code == 403
    assert "schedule sessions for themselves" in response.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_sessions_teacher_filter(client):
    """Verify that listing sessions returns only the teacher's sessions for teacher users."""
    mock_teacher = MagicMock()
    mock_teacher.id = 2
    mock_teacher.role = "teacher"
    mock_teacher.email = "teacher@example.com"
    mock_teacher.name = "Teacher Name"

    mock_session = MagicMock()
    mock_session.id = 10
    mock_session.title = "Geometry Session"
    mock_session.description = "Geometry basics"
    mock_session.date = "2026-07-27T10:00:00Z"
    mock_session.teacher_id = 2
    mock_session.student_id = 3
    mock_session.teacher = mock_teacher

    mock_student = MagicMock()
    mock_student.id = 3
    mock_student.role = "student"
    mock_student.email = "student@example.com"
    mock_student.name = "Student Name"
    mock_session.student = mock_student

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_session]

    async def mock_execute(*args, **kwargs):
        return mock_result

    mock_db = MagicMock()
    mock_db.execute = mock_execute

    app.dependency_overrides[get_current_user] = lambda: mock_teacher
    app.dependency_overrides[get_db] = lambda: mock_db

    headers = {"Authorization": "Bearer mock-token"}
    response = await client.get("/api/v1/sessions/", headers=headers)
    assert response.status_code == 200
    res_list = response.json()
    assert len(res_list) == 1
    assert res_list[0]["title"] == "Geometry Session"

    app.dependency_overrides.clear()

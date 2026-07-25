import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.deps import check_session_access, get_current_user, get_db
from app.main import app


@pytest.mark.asyncio
async def test_trigger_evaluation_success(client):
    """Verify that an admin or teacher can trigger an evaluation.

    Produces a DB record and enqueues a job.
    """
    mock_db = AsyncMock()

    mock_teacher = MagicMock()
    mock_teacher.id = 2
    mock_teacher.role = "teacher"

    mock_session = MagicMock()
    mock_session.id = 10
    mock_session.teacher_id = 2
    mock_session.student_id = 3

    # Mock refresh to set ID and status fields on save
    async def mock_refresh(instance):
        instance.id = 5
        instance.status = "Pending"
        instance.created_at = datetime.datetime.now(datetime.UTC)

    mock_db.refresh = mock_refresh

    app.dependency_overrides[get_current_user] = lambda: mock_teacher
    app.dependency_overrides[check_session_access] = lambda: mock_session
    app.dependency_overrides[get_db] = lambda: mock_db

    # Patch the global Redis queue inside evaluations module
    with patch(
        "app.api.v1.endpoints.evaluations.evaluation_queue.enqueue", new_callable=AsyncMock
    ) as mock_enqueue:
        headers = {"Authorization": "Bearer mock-token"}
        response = await client.post("/api/v1/evaluations/trigger/10", headers=headers)

        assert response.status_code == 201
        res_data = response.json()
        assert res_data["session_id"] == 10
        assert res_data["status"] == "Pending"
        assert res_data["id"] == 5

        # Check that Redis received the session ID string to process
        mock_enqueue.assert_called_once_with("10")

    app.dependency_overrides.clear()

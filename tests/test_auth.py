from unittest.mock import MagicMock

import pytest

from app.api.deps import get_db
from app.core.security import get_password_hash
from app.main import app


@pytest.mark.asyncio
async def test_register_user(client):
    """Verify that a user can successfully register with correct details."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None

    async def mock_execute(*args, **kwargs):
        return mock_result

    mock_db = MagicMock()
    mock_db.execute = mock_execute
    mock_db.add = MagicMock()

    async def mock_commit():
        pass

    async def mock_refresh(instance):
        instance.id = 1

    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh

    app.dependency_overrides[get_db] = lambda: mock_db

    register_data = {
        "email": "teacher1@example.com",
        "password": "password123",
        "name": "Teacher One",
        "role": "teacher",
    }

    response = await client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["email"] == "teacher1@example.com"
    assert res_data["name"] == "Teacher One"
    assert res_data["role"] == "teacher"
    assert res_data["id"] == 1

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_user(client):
    """Verify that a registered user can successfully authenticate and receive a JWT token."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "teacher1@example.com"
    mock_user.name = "Teacher One"
    mock_user.role = "teacher"
    mock_user.hashed_password = get_password_hash("password123")

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user

    async def mock_execute(*args, **kwargs):
        return mock_result

    mock_db = MagicMock()
    mock_db.execute = mock_execute

    app.dependency_overrides[get_db] = lambda: mock_db

    login_data = {"username": "teacher1@example.com", "password": "password123"}

    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    res_data = response.json()
    assert "access_token" in res_data
    assert res_data["token_type"] == "bearer"

    app.dependency_overrides.clear()

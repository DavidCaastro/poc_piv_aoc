"""Shared fixtures for all tests.

Sets up JWT_SECRET_KEY, test client, and token helpers for each role.
Resets in-memory state before each test to ensure isolation.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Set JWT secret BEFORE any app imports
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from src.main import app  # noqa: E402
from src.data.store import reset_store  # noqa: E402


@pytest.fixture(autouse=True)
def clean_state():
    """Reset all in-memory state before each test."""
    reset_store()
    yield
    reset_store()


@pytest.fixture
def client():
    """FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client):
    """Get a valid access token for ADMIN role."""
    r = client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "Admin123!",
    })
    return r.json()["access_token"]


@pytest.fixture
def admin_tokens(client):
    """Get full token pair (access + refresh) for ADMIN role."""
    r = client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "Admin123!",
    })
    return r.json()


@pytest.fixture
def editor_token(client):
    """Get a valid access token for EDITOR role."""
    r = client.post("/auth/login", json={
        "email": "editor@test.com",
        "password": "Editor123!",
    })
    return r.json()["access_token"]


@pytest.fixture
def viewer_token(client):
    """Get a valid access token for VIEWER role."""
    r = client.post("/auth/login", json={
        "email": "viewer@test.com",
        "password": "Viewer123!",
    })
    return r.json()["access_token"]


def auth_header(token: str) -> dict:
    """Build Authorization header."""
    return {"Authorization": f"Bearer {token}"}

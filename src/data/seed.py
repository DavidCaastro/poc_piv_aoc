"""Seed data: predefined test users with BCrypt-hashed passwords.

Users defined here are loaded into the in-memory store at startup.
Passwords are hashed with BCrypt cost factor 12 as required by RF-04.

Predefined users (from project_spec.md):
  admin@test.com  / Admin123!  -> ADMIN
  editor@test.com / Editor123! -> EDITOR
  viewer@test.com / Viewer123! -> VIEWER
"""

import bcrypt

from src.schemas.roles import Role
from src.schemas.users import UserInDB


def _hash_password(plain_password: str) -> str:
    """Hash a password with BCrypt cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


# Pre-computed hashes to avoid re-hashing on every import.
# These are generated once at first import.
_SEED_USERS: list[dict] | None = None


def _build_seed_users() -> list[UserInDB]:
    """Build seed users with hashed passwords."""
    return [
        UserInDB(
            id="user_admin_001",
            email="admin@test.com",
            hashed_password=_hash_password("Admin123!"),
            role=Role.ADMIN,
        ),
        UserInDB(
            id="user_editor_001",
            email="editor@test.com",
            hashed_password=_hash_password("Editor123!"),
            role=Role.EDITOR,
        ),
        UserInDB(
            id="user_viewer_001",
            email="viewer@test.com",
            hashed_password=_hash_password("Viewer123!"),
            role=Role.VIEWER,
        ),
    ]


def seed_users() -> None:
    """Populate the user store with predefined test users."""
    from src.data import store

    for user in _build_seed_users():
        store.users[user.email] = user


# Auto-seed on first import
seed_users()

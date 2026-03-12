"""Role and Permission enums for RBAC (RF-05)."""

from enum import Enum


class Role(str, Enum):
    """User roles with hierarchy: ADMIN > EDITOR > VIEWER."""

    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


# Hierarchy mapping: higher value = more privileges
ROLE_HIERARCHY: dict[Role, int] = {
    Role.VIEWER: 1,
    Role.EDITOR: 2,
    Role.ADMIN: 3,
}

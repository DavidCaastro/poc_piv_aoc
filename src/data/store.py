"""Global in-memory state store.

All application data lives here. No external database.
This module is the single source of truth for mutable state.

DESIGN DECISIONS:
- revoked_tokens: dict[str, float] indexed by jti for O(1) lookup (RF-03).
  A list would require O(n) search which is unacceptable.
- rate_windows: dict[str, list[float]] for sliding window rate limiting (RF-07).
- audit_log: list[dict] for immutable append-only audit trail (RF-08).
- users: dict[str, UserInDB] indexed by email for O(1) lookup.
- resources: list[dict] for simple in-memory CRUD (RF-06).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schemas.users import UserInDB

# User store: email -> UserInDB
# Populated by seed.py at module load time
users: dict[str, "UserInDB"] = {}

# Resources store: list of resource dicts
# Each dict: {"id": int, "title": str, "description": str, "owner_id": str}
resources: list[dict] = []

# Resource ID counter
_next_resource_id: int = 1

# Revoked tokens cache: jti -> expiry unix timestamp
# STRUCTURE: dict (hashmap) — O(1) per key
# JUSTIFICATION: The critical operation is lookup by token ID (jti).
# A dict guarantees O(1) for insert, lookup and delete by string key.
# A list/array would be O(n) for search by value — unacceptable.
revoked_tokens: dict[str, float] = {}

# Rate limiting windows: user_id -> list of request timestamps
# Used for sliding window rate limiting per user
rate_windows: dict[str, list[float]] = {}

# Audit trail: append-only log of authenticated requests (RF-08)
# Each entry: {"user_id": str, "role": str, "endpoint": str,
#              "method": str, "timestamp": str, "status_code": int}
audit_log: list[dict] = []


def get_next_resource_id() -> int:
    """Return and increment the resource ID counter."""
    global _next_resource_id
    current = _next_resource_id
    _next_resource_id += 1
    return current


def reset_store() -> None:
    """Reset all in-memory state. Used by tests."""
    global _next_resource_id
    users.clear()
    resources.clear()
    revoked_tokens.clear()
    rate_windows.clear()
    audit_log.clear()
    _next_resource_id = 1

    # Re-seed after reset
    from src.data.seed import seed_users
    seed_users()

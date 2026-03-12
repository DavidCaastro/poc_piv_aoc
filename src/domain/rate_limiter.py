"""Rate Limiter — Sliding Window per User (RF-07).

In-memory rate limiting using dict[user_id -> list[timestamps]].
Limits are based on the user's role:
  - VIEWER: 10 requests/minute
  - EDITOR: 30 requests/minute
  - ADMIN: 100 requests/minute

Returns HTTP 429 when limit is exceeded.
"""

import time

from src.data import store
from src.schemas.roles import Role


# Rate limits per role (requests per minute) — RF-07
RATE_LIMITS: dict[Role, int] = {
    Role.VIEWER: 10,
    Role.EDITOR: 30,
    Role.ADMIN: 100,
}

# Sliding window size in seconds
_WINDOW_SECONDS: float = 60.0


def check_rate_limit(user_id: str, role: str) -> bool:
    """Check if a user has exceeded their rate limit.

    Uses sliding window: counts requests in the last 60 seconds.
    Expired timestamps are pruned on each call.

    Args:
        user_id: Unique user identifier (from JWT "sub" claim)
        role: Role string from JWT token (e.g., "ADMIN")

    Returns:
        True if the request is ALLOWED (within limit).
        False if the request should be REJECTED (limit exceeded -> HTTP 429).
    """
    now = time.time()
    cutoff = now - _WINDOW_SECONDS

    # Get or create the user's request window
    if user_id not in store.rate_windows:
        store.rate_windows[user_id] = []

    window = store.rate_windows[user_id]

    # Prune expired timestamps (sliding window cleanup)
    store.rate_windows[user_id] = [ts for ts in window if ts > cutoff]
    window = store.rate_windows[user_id]

    # Determine limit for this role
    try:
        user_role = Role(role)
    except ValueError:
        # Unknown role -> deny (most restrictive limit)
        return False

    limit = RATE_LIMITS.get(user_role, 10)

    # Check if within limit
    if len(window) >= limit:
        return False

    # Record this request
    window.append(now)
    return True

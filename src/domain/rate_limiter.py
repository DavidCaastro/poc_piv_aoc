"""Rate Limiter — Sliding Window per User (RF-07).

Two backends depending on environment:
  - Redis (Upstash): used when UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN are set.
    Persists rate windows across server restarts. Used in production (Render).
  - In-memory: fallback when Redis env vars are absent.
    Used in tests and local development without credentials.

Limits per role (requests per minute):
  - VIEWER: 10 | EDITOR: 30 | ADMIN: 100

Login rate limit (per IP): 10 attempts / 15 minutes.
"""

import os
import time
import uuid

from src.data import store
from src.schemas.roles import Role


# ---------------------------------------------------------------------------
# Redis backend (optional)
# ---------------------------------------------------------------------------

_REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "")
_REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
_USE_REDIS = bool(_REDIS_URL and _REDIS_TOKEN)

if _USE_REDIS:
    from upstash_redis import Redis
    _redis = Redis(url=_REDIS_URL, token=_REDIS_TOKEN)


def _redis_sliding_window(key: str, limit: int, window_seconds: float) -> bool:
    """Sliding window check using Redis sorted sets.

    Members are unique UUIDs; scores are Unix timestamps.
    Expired members are pruned on each call.
    Not atomic (acceptable for portfolio/demo use).
    """
    now = time.time()
    cutoff = now - window_seconds

    _redis.zremrangebyscore(key, 0, cutoff)
    count = _redis.zcard(key)

    if count >= limit:
        return False

    _redis.zadd(key, {str(uuid.uuid4()): now})
    _redis.expire(key, int(window_seconds) + 1)
    return True


# ---------------------------------------------------------------------------
# Rate limits per role (RF-07)
# ---------------------------------------------------------------------------

RATE_LIMITS: dict[Role, int] = {
    Role.VIEWER: 10,
    Role.EDITOR: 30,
    Role.ADMIN: 100,
}

_WINDOW_SECONDS: float = 60.0


def check_rate_limit(user_id: str, role: str) -> bool:
    """Check if a user has exceeded their rate limit.

    Uses sliding window (60 s). Backend: Redis if configured, in-memory otherwise.

    Args:
        user_id: Unique user identifier (from JWT "sub" claim)
        role: Role string from JWT token (e.g., "ADMIN")

    Returns:
        True if the request is ALLOWED. False if limit exceeded -> HTTP 429.
    """
    try:
        user_role = Role(role)
    except ValueError:
        return False

    limit = RATE_LIMITS.get(user_role, 10)

    if _USE_REDIS:
        return _redis_sliding_window(f"rate:{user_id}", limit, _WINDOW_SECONDS)

    # In-memory fallback
    now = time.time()
    cutoff = now - _WINDOW_SECONDS
    if user_id not in store.rate_windows:
        store.rate_windows[user_id] = []
    store.rate_windows[user_id] = [ts for ts in store.rate_windows[user_id] if ts > cutoff]
    if len(store.rate_windows[user_id]) >= limit:
        return False
    store.rate_windows[user_id].append(now)
    return True


# ---------------------------------------------------------------------------
# Login rate limit — per IP (FIX VULN-007)
# ---------------------------------------------------------------------------

_LOGIN_LIMIT: int = 10
_LOGIN_WINDOW_SECONDS: float = 900.0  # 15 minutes


def check_login_rate_limit(client_ip: str) -> bool:
    """Check if a client IP has exceeded the login attempt rate limit.

    Sliding window (15 min). Backend: Redis if configured, in-memory otherwise.

    Args:
        client_ip: Client IP address from the HTTP request.

    Returns:
        True if the request is ALLOWED. False if limit exceeded -> HTTP 429.
    """
    if _USE_REDIS:
        return _redis_sliding_window(f"login:{client_ip}", _LOGIN_LIMIT, _LOGIN_WINDOW_SECONDS)

    # In-memory fallback
    now = time.time()
    cutoff = now - _LOGIN_WINDOW_SECONDS
    window = [t for t in store.login_windows.get(client_ip, []) if t > cutoff]
    if len(window) >= _LOGIN_LIMIT:
        return False
    window.append(now)
    store.login_windows[client_ip] = window
    return True

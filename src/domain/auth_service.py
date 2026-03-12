"""Authentication service (RF-01, RF-02, RF-03, RF-04).

Handles login, JWT token creation/verification, and token revocation.
This module is in the Domain layer — it must NOT import from transport/.

Security patterns applied:
- BCrypt with cost factor >= 12
- Timing-safe password verification (always runs even if user doesn't exist)
- JWT with jti for revocation support
- Generic error messages (never distinguish email vs password failure)
- JWT_SECRET_KEY from environment variable only
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from src.data import store
from src.schemas.roles import Role
from src.schemas.tokens import TokenPayload, TokenPair
from src.schemas.users import UserInDB


# JWT configuration
_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 60      # 1 hour (RF-01)
_REFRESH_TOKEN_EXPIRE_MINUTES = 1440   # 24 hours (RF-01)

# Dummy hash for timing-safe comparison when user doesn't exist (RF-04).
# Generated with BCrypt cost 12 so the timing matches real verification.
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password-for-timing-safety", bcrypt.gensalt(rounds=12)).decode("utf-8")


def _get_secret_key() -> str:
    """Get JWT secret key from environment. Re-read each time for test flexibility."""
    return os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-testing-only")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Timing-safe password verification using BCrypt (RF-04).

    Always uses bcrypt.checkpw which is constant-time for the same hash cost.
    Never compare passwords as plain strings.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def login(email: str, password: str) -> TokenPair | None:
    """Authenticate user and return token pair (RF-01).

    Security: Always executes verify_password even if user doesn't exist
    to prevent timing-based user enumeration (RF-04).

    Returns:
        TokenPair if credentials are valid, None otherwise.
    """
    user = store.users.get(email)

    # Anti-timing attack: always execute BCrypt verification (RF-04)
    # If user doesn't exist, compare against dummy hash
    candidate_hash = user.hashed_password if user else _DUMMY_HASH

    password_valid = verify_password(password, candidate_hash)

    if user is None or not password_valid:
        return None

    return create_token_pair(user)


def create_token_pair(user: UserInDB) -> TokenPair:
    """Generate access + refresh token pair for a user (RF-01)."""
    access_token = _create_token(
        user=user,
        token_type="access",
        expires_delta=timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = _create_token(
        user=user,
        token_type="refresh",
        expires_delta=timedelta(minutes=_REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


def _create_token(user: UserInDB, token_type: str, expires_delta: timedelta) -> str:
    """Create a single JWT token with the agreed schema.

    JWT claims schema (agreed with T-03 via CoherenceAgent):
    {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "jti": uuid4 string,
        "type": "access" | "refresh",
        "exp": unix timestamp
    }
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "jti": str(uuid.uuid4()),
        "type": token_type,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, _get_secret_key(), algorithm=_ALGORITHM)


def verify_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token.

    Raises:
        JWTError: If the token is invalid, expired, or has been revoked.
    """
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[_ALGORITHM])
    except JWTError:
        raise

    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        raise JWTError("Token has been revoked")

    return TokenPayload(
        sub=payload["sub"],
        email=payload["email"],
        role=payload["role"],
        jti=payload["jti"],
        type=payload["type"],
        exp=payload["exp"],
    )


def revoke_token(jti: str, exp: float) -> None:
    """Add a token's jti to the revoked tokens cache (RF-03).

    Uses dict indexed by jti for O(1) lookup.
    """
    store.revoked_tokens[jti] = exp


def is_token_revoked(jti: str) -> bool:
    """Check if a token has been revoked (RF-03).

    O(1) lookup in dict indexed by jti.
    """
    return jti in store.revoked_tokens


def refresh_tokens(refresh_token_str: str) -> TokenPair | None:
    """Validate a refresh token and issue a new token pair (RF-02).

    The old refresh token's jti is revoked after issuing a new pair.

    Returns:
        New TokenPair if refresh token is valid, None otherwise.
    """
    try:
        payload = verify_token(refresh_token_str)
    except JWTError:
        return None

    if payload.type != "refresh":
        return None

    # Find the user
    user = None
    for u in store.users.values():
        if u.id == payload.sub:
            user = u
            break

    if user is None:
        return None

    # Revoke the old refresh token
    revoke_token(payload.jti, payload.exp)

    # Issue new token pair
    return create_token_pair(user)

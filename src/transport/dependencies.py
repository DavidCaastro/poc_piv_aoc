"""FastAPI dependencies for auth, RBAC, and rate limiting.

Dependency chain order (CRITICAL for security):
1. Auth verification (decode JWT, check revocation)
2. RBAC check (verify role has permission for endpoint)
3. Rate limit check (verify user within rate window)

This module is in the Transport layer. It delegates all logic to Domain services.
"""

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import jwt

from src.data import store
from src.domain import auth_service
from src.domain.rbac_engine import check_permission
from src.domain.rate_limiter import check_rate_limit
from src.schemas.tokens import TokenPayload


_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> TokenPayload:
    """Step 1: Authenticate — decode JWT and verify it's not revoked.

    Raises HTTP 401 with generic message if token is invalid or revoked.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = auth_service.verify_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def check_rbac(
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Step 2: RBAC — verify role has permission for this endpoint/method.

    Raises HTTP 403 if the user's role lacks permission.
    """
    endpoint = request.url.path
    method = request.method

    if not check_permission(current_user.role, endpoint, method):
        store.audit_log.append({
            "user_id": current_user.sub,
            "role": current_user.role,
            "endpoint": endpoint,
            "method": method,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_code": 403,
            "event": "rbac_denied",
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes.",
        )

    return current_user


async def check_rate(
    request: Request,
    current_user: TokenPayload = Depends(check_rbac),
) -> TokenPayload:
    """Step 3: Rate Limiting — verify user is within their rate window.

    Raises HTTP 429 if the user has exceeded their rate limit.
    Chain: auth -> rbac -> rate_limit (correct order).
    """
    if not check_rate_limit(current_user.sub, current_user.role):
        store.audit_log.append({
            "user_id": current_user.sub,
            "role": current_user.role,
            "endpoint": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_code": 429,
            "event": "rate_limit_exceeded",
        })
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Limite de solicitudes excedido.",
        )

    # Log to audit trail (RF-08)
    # KNOWN LIMITATION: status_code is recorded as 200 at dependency resolution time.
    # Errors raised downstream (404, 500) are not captured here.
    # For complete audit logging, implement a response middleware.
    store.audit_log.append({
        "user_id": current_user.sub,
        "role": current_user.role,
        "endpoint": request.url.path,
        "method": request.method,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status_code": 200,
    })

    return current_user


# Alias for the full dependency chain
# Use this as Depends(require_auth) in protected endpoints
require_auth = check_rate

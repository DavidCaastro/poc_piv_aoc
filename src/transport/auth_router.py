"""Auth endpoints: login, refresh, logout (RF-01, RF-02, RF-03).

These endpoints handle authentication. Login is public (no auth required).
Refresh and logout require a valid token.
"""

from datetime import datetime, timezone

import jwt

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.data import store
from src.domain import auth_service
from src.domain import rate_limiter
from src.schemas.tokens import TokenPair, RefreshRequest, LogoutRequest, TokenPayload
from src.schemas.users import LoginRequest
from src.transport.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(body: LoginRequest, request: Request):
    """POST /auth/login — Authenticate user and return token pair (RF-01).

    No auth required. Returns generic 401 on failure (RF-04, RF-09).
    FIX VULN-006: Rate limited per client IP (10 attempts / 15 minutes).
    FIX VULN-012: Failed login attempts are recorded in the audit log.
    """
    # FIX VULN-006: IP-based rate limiting for login endpoint
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.check_login_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intenta de nuevo más tarde.",
        )

    result = auth_service.login(body.email, body.password)

    if result is None:
        # FIX VULN-012: Record failed login attempt in audit log
        store.audit_log.append({
            "user_id": None,
            "email_attempted": body.email,
            "role": None,
            "endpoint": "/auth/login",
            "method": "POST",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_code": 401,
            "event": "login_failed",
        })
        # RF-04: Generic message — never distinguish email vs password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest):
    """POST /auth/refresh — Get new token pair from refresh token (RF-02, RF-12).

    Validates the refresh token, revokes it, and issues a new pair.
    Records the attempt in the audit log regardless of outcome.
    """
    # RF-12: Capture user identity from token before consuming it
    user_id, role = None, None
    try:
        refresh_payload = auth_service.verify_token(body.refresh_token)
        if refresh_payload.type == "refresh":
            user_id = refresh_payload.sub
            role = refresh_payload.role
    except jwt.PyJWTError:
        pass

    result = auth_service.refresh_tokens(body.refresh_token)

    if result is None:
        store.audit_log.append({
            "user_id": user_id,
            "role": role,
            "endpoint": "/auth/refresh",
            "method": "POST",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_code": 401,
            "event": "token_refresh_failed",
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    store.audit_log.append({
        "user_id": user_id,
        "role": role,
        "endpoint": "/auth/refresh",
        "method": "POST",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status_code": 200,
        "event": "token_refreshed",
    })
    return result


@router.post("/logout")
async def logout(
    body: LogoutRequest = None,
    current_user: TokenPayload = Depends(get_current_user),
):
    """POST /auth/logout — Revoke the current access token (RF-03).

    FIX VULN-015: Also revokes the refresh token if provided in the request body.
    Adds both tokens' jtis to the revoked tokens cache (O(1) dict).
    """
    auth_service.revoke_token(current_user.jti, current_user.exp)

    # FIX VULN-015: Revoke refresh token if provided
    if body and body.refresh_token:
        try:
            refresh_payload = auth_service.verify_token(body.refresh_token)
            if refresh_payload.type == "refresh":
                auth_service.revoke_token(refresh_payload.jti, refresh_payload.exp)
        except jwt.PyJWTError:
            # Invalid refresh token — access token already revoked, proceed
            pass

    return {"detail": "Token revocado exitosamente."}

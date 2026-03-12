"""Token schemas for JWT authentication (RF-01, RF-02, RF-03).

JWT claims schema (agreed for coherence between T-02 and T-03):
{
    "sub": "user_id",        # string - unique user identifier
    "email": "user@test.com", # string
    "role": "ADMIN",          # string - Role enum value
    "jti": "uuid4-string",    # string - JWT ID for revocation
    "type": "access",         # string - "access" | "refresh"
    "exp": 1234567890         # int - unix timestamp
}
"""

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    sub: str = Field(..., description="User ID (subject)")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role (ADMIN, EDITOR, VIEWER)")
    jti: str = Field(..., description="JWT ID for revocation support")
    type: str = Field(..., description="Token type: 'access' or 'refresh'")
    exp: int = Field(..., description="Expiration timestamp (unix)")


class TokenPair(BaseModel):
    """Response containing access and refresh tokens (RF-01)."""

    access_token: str = Field(..., description="JWT access token (1h expiry)")
    refresh_token: str = Field(..., description="JWT refresh token (24h expiry)")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'")


class RefreshRequest(BaseModel):
    """Request body for POST /auth/refresh (RF-02)."""

    refresh_token: str = Field(..., description="Valid, non-revoked refresh token")

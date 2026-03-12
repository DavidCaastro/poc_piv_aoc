"""User schemas (RF-01, RF-04)."""

from pydantic import BaseModel, EmailStr, Field

from src.schemas.roles import Role


class UserInDB(BaseModel):
    """Internal user representation with hashed password.

    WARNING: hashed_password must NEVER be exposed in API responses.
    """

    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    hashed_password: str = Field(..., description="BCrypt hashed password (cost >= 12)")
    role: Role = Field(..., description="User role for RBAC")


class LoginRequest(BaseModel):
    """Request body for POST /auth/login (RF-01)."""

    email: EmailStr = Field(
        ...,
        description="User email address",
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User password",
    )

    model_config = {"extra": "forbid"}


class UserResponse(BaseModel):
    """Public user representation — excludes hashed_password."""

    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    role: Role = Field(..., description="User role")

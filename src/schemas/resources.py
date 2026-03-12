"""Resource schemas for CRUD operations (RF-06)."""

from pydantic import BaseModel, Field


class Resource(BaseModel):
    """Full resource representation."""

    id: int = Field(..., description="Resource ID")
    title: str = Field(..., description="Resource title")
    description: str = Field(default="", description="Resource description")
    owner_id: str = Field(..., description="ID of the user who created the resource")


class ResourceCreate(BaseModel):
    """Request body for POST /resources."""

    title: str = Field(..., min_length=1, description="Resource title")
    description: str = Field(default="", description="Resource description")

    model_config = {"extra": "forbid"}


class ResourceUpdate(BaseModel):
    """Request body for PUT /resources/{id}."""

    title: str | None = Field(default=None, min_length=1, description="New title")
    description: str | None = Field(default=None, description="New description")

    model_config = {"extra": "forbid"}

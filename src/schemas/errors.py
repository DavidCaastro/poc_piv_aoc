"""Error response schemas (RF-09).

All error messages are generic and do not reveal sensitive information.
"""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Unified error response schema.

    Messages MUST be generic:
    - 401: "Credenciales invalidas." (never distinguish email vs password)
    - 403: "Permisos insuficientes."
    - 429: "Limite de solicitudes excedido."
    """

    detail: str = Field(
        ...,
        description="Generic error message. Never reveals sensitive information.",
    )

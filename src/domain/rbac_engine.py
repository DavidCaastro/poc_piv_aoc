"""RBAC Engine — Role-Based Access Control (RF-05, RF-06).

Explicit, centralized permission matrix. Default-deny for unlisted endpoints.
This module is in the Domain layer — it must NOT import from transport/.

The "role" field from JWT tokens (string) is converted to Role enum
for permission checks. Schema agreed with T-02 (auth-service) via CoherenceAgent.
"""

from src.schemas.roles import Role, ROLE_HIERARCHY


# ============================================================================
# PERMISSION MATRIX (RF-05 + RF-06)
# ============================================================================
# Key: (endpoint_pattern, HTTP method)
# Value: minimum Role required (by hierarchy)
#
# Any endpoint/method combination NOT in this matrix is DENIED by default.
# ============================================================================

_PERMISSION_MATRIX: dict[tuple[str, str], Role] = {
    # Resources endpoints (RF-06)
    ("/resources", "GET"): Role.VIEWER,
    ("/resources", "POST"): Role.EDITOR,
    ("/resources/{id}", "PUT"): Role.EDITOR,
    ("/resources/{id}", "DELETE"): Role.ADMIN,
    # Admin endpoints (RF-08)
    ("/admin/audit-log", "GET"): Role.ADMIN,
}


def _normalize_endpoint(endpoint: str) -> str:
    """Normalize endpoint path for matching against permission matrix.

    Converts specific resource IDs to {id} placeholder.
    Example: /resources/42 -> /resources/{id}
    """
    parts = endpoint.rstrip("/").split("/")

    # Match /resources/{numeric_id} pattern
    if len(parts) == 3 and parts[1] == "resources":
        try:
            int(parts[2])
            return "/resources/{id}"
        except ValueError:
            pass

    return endpoint.rstrip("/") or "/"


def check_permission(role: str, endpoint: str, method: str) -> bool:
    """Check if a role has permission for the given endpoint and method.

    Args:
        role: Role string from JWT token (e.g., "ADMIN", "EDITOR", "VIEWER")
        endpoint: Request path (e.g., "/resources", "/resources/42")
        method: HTTP method (e.g., "GET", "POST", "PUT", "DELETE")

    Returns:
        True if the role has sufficient permission, False otherwise.
        Unlisted endpoints are DENIED by default.
    """
    try:
        user_role = Role(role)
    except ValueError:
        return False

    normalized = _normalize_endpoint(endpoint)
    required_role = _PERMISSION_MATRIX.get((normalized, method.upper()))

    if required_role is None:
        # Endpoint/method not in matrix -> default deny
        return False

    # Check hierarchy: user's role level must be >= required role level
    return ROLE_HIERARCHY[user_role] >= ROLE_HIERARCHY[required_role]


def get_required_role(endpoint: str, method: str) -> Role | None:
    """Get the minimum required role for an endpoint/method combination.

    Returns:
        The minimum Role required, or None if the endpoint is not in the matrix.
    """
    normalized = _normalize_endpoint(endpoint)
    return _PERMISSION_MATRIX.get((normalized, method.upper()))

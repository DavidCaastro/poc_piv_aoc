"""Tests for security headers and input validation boundaries.

Covers FIX VULN-004 (security headers), FIX VULN-018 (field length limits),
and FIX VULN-020 (password length limit).
"""

import pytest
from tests.conftest import auth_header


class TestSecurityHeaders:
    """FIX VULN-004: Security headers are present on every response."""

    def test_security_headers_on_public_endpoint(self, client):
        """Security headers are present even on unauthenticated responses."""
        r = client.get("/docs")
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert r.headers.get("x-xss-protection") == "0"

    def test_security_headers_on_authenticated_endpoint(self, client, admin_token):
        """Security headers are present on authenticated API responses."""
        r = client.get("/resources", headers=auth_header(admin_token))
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert r.headers.get("x-xss-protection") == "0"

    def test_security_headers_on_error_response(self, client):
        """Security headers are present on 401 error responses."""
        r = client.get("/resources")  # No token → 401
        assert r.status_code == 401
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"


class TestInputValidation:
    """FIX VULN-018/020: Input length boundaries enforced at schema level."""

    def test_title_exceeds_max_length_returns_422(self, client, editor_token):
        """title > 200 chars is rejected with 422."""
        r = client.post(
            "/resources",
            json={"title": "x" * 201},
            headers=auth_header(editor_token),
        )
        assert r.status_code == 422

    def test_title_at_max_length_is_accepted(self, client, editor_token):
        """title at exactly 200 chars is accepted."""
        r = client.post(
            "/resources",
            json={"title": "x" * 200},
            headers=auth_header(editor_token),
        )
        assert r.status_code == 201

    def test_title_empty_returns_422(self, client, editor_token):
        """title min_length=1 — empty string rejected with 422."""
        r = client.post(
            "/resources",
            json={"title": ""},
            headers=auth_header(editor_token),
        )
        assert r.status_code == 422

    def test_description_exceeds_max_length_returns_422(self, client, editor_token):
        """description > 5000 chars is rejected with 422."""
        r = client.post(
            "/resources",
            json={"title": "Valid Title", "description": "x" * 5001},
            headers=auth_header(editor_token),
        )
        assert r.status_code == 422

    def test_description_at_max_length_is_accepted(self, client, editor_token):
        """description at exactly 5000 chars is accepted."""
        r = client.post(
            "/resources",
            json={"title": "Valid Title", "description": "x" * 5000},
            headers=auth_header(editor_token),
        )
        assert r.status_code == 201

    def test_password_exceeds_max_length_returns_422(self, client):
        """FIX VULN-020: password > 72 chars is rejected with 422 (prevents bcrypt ValueError)."""
        r = client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "A" * 73},
        )
        assert r.status_code == 422

    def test_password_at_max_length_is_accepted(self, client):
        """password at exactly 72 chars passes schema validation (auth fails with 401, not 422/500)."""
        r = client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "A" * 72},
        )
        # Schema validation passes (no 422/500); auth fails with 401 — expected
        assert r.status_code == 401

    def test_extra_fields_in_resource_body_rejected(self, client, editor_token):
        """extra='forbid': unknown fields in resource request body are rejected with 422."""
        r = client.post(
            "/resources",
            json={"title": "Valid", "malicious_field": "injected"},
            headers=auth_header(editor_token),
        )
        assert r.status_code == 422

    def test_extra_fields_in_login_body_rejected(self, client):
        """extra='forbid': unknown fields in login request body are rejected with 422."""
        r = client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "Admin123!", "extra": "injected"},
        )
        assert r.status_code == 422

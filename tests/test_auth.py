"""Tests for authentication: login, refresh, logout, token revocation.

Covers RF-01, RF-02, RF-03, RF-04, RF-09, and RF-10 scenarios.
"""

import time

import jwt as pyjwt
import pytest
from tests.conftest import auth_header


class TestLogin:
    """RF-01: POST /auth/login returns access_token + refresh_token."""

    def test_login_success(self, client):
        r = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "Admin123!",
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """RF-04: Wrong password returns 401 with generic message."""
        r = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "WrongPassword!",
        })
        assert r.status_code == 401
        assert r.json()["detail"] == "Credenciales invalidas."

    def test_login_nonexistent_user(self, client):
        """RF-04: Non-existent user returns same 401 as wrong password."""
        r = client.post("/auth/login", json={
            "email": "nobody@test.com",
            "password": "AnyPassword!",
        })
        assert r.status_code == 401
        assert r.json()["detail"] == "Credenciales invalidas."

    def test_login_error_message_is_generic(self, client):
        """RF-04, RF-09: Error message does not reveal which field failed."""
        r_wrong_pass = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "wrong",
        })
        r_wrong_user = client.post("/auth/login", json={
            "email": "nobody@test.com",
            "password": "anything",
        })
        # Both must return the same generic message
        assert r_wrong_pass.json()["detail"] == r_wrong_user.json()["detail"]

        # Message must not contain revealing words
        detail = r_wrong_pass.json()["detail"].lower()
        for word in ["email", "password", "usuario", "user", "pass"]:
            assert word not in detail, f"Error reveals: '{word}'"

    def test_login_all_roles(self, client):
        """All 3 predefined users can log in."""
        users = [
            ("admin@test.com", "Admin123!"),
            ("editor@test.com", "Editor123!"),
            ("viewer@test.com", "Viewer123!"),
        ]
        for email, password in users:
            r = client.post("/auth/login", json={"email": email, "password": password})
            assert r.status_code == 200, f"Failed for {email}"

    def test_login_rate_limit_per_ip(self, client):
        """FIX VULN-006: After 10 login attempts from same IP -> 429."""
        for _ in range(10):
            client.post("/auth/login", json={"email": "nobody@test.com", "password": "Wrong!"})
        # 11th attempt is blocked — even with valid credentials
        r = client.post("/auth/login", json={"email": "admin@test.com", "password": "Admin123!"})
        assert r.status_code == 429
        assert "intentos" in r.json()["detail"].lower()

    def test_failed_login_recorded_in_audit_log(self, client, admin_token):
        """FIX VULN-012: Failed login attempts appear in audit log with event=login_failed."""
        client.post("/auth/login", json={"email": "attacker@evil.com", "password": "WrongPass!"})

        r = client.get("/admin/audit-log", headers=auth_header(admin_token))
        assert r.status_code == 200
        logs = r.json()
        failed_entries = [e for e in logs if e.get("event") == "login_failed"]
        assert len(failed_entries) >= 1
        entry = failed_entries[0]
        assert entry["user_id"] is None
        assert entry["role"] is None
        assert entry["status_code"] == 401


class TestRefresh:
    """RF-02: POST /auth/refresh accepts valid refresh_token."""

    def test_refresh_success(self, client, admin_tokens):
        r = client.post("/auth/refresh", json={
            "refresh_token": admin_tokens["refresh_token"],
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_with_invalid_token(self, client):
        """RF-10 scenario: Refresh with invalid token -> 401."""
        r = client.post("/auth/refresh", json={
            "refresh_token": "invalid.token.here",
        })
        assert r.status_code == 401

    def test_refresh_with_access_token_fails(self, client, admin_tokens):
        """Access token cannot be used as refresh token."""
        r = client.post("/auth/refresh", json={
            "refresh_token": admin_tokens["access_token"],
        })
        assert r.status_code == 401

    def test_refresh_revokes_old_token(self, client, admin_tokens):
        """After refresh, old refresh token is revoked."""
        old_refresh = admin_tokens["refresh_token"]
        # First refresh succeeds
        r1 = client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert r1.status_code == 200
        # Second refresh with same token fails (revoked)
        r2 = client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert r2.status_code == 401


class TestLogout:
    """RF-03: POST /auth/logout revokes the active token."""

    def test_logout_success(self, client, admin_token):
        r = client.post("/auth/logout", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_revoked_token_cannot_access(self, client, admin_token):
        """RF-10 scenario: Token revocado intentando acceder -> 401."""
        # Logout (revoke token)
        client.post("/auth/logout", headers=auth_header(admin_token))
        # Try to use revoked token
        r = client.get("/resources", headers=auth_header(admin_token))
        assert r.status_code == 401

    def test_logout_without_token(self, client):
        """Logout without token returns 401."""
        r = client.post("/auth/logout")
        assert r.status_code == 401

    def test_logout_also_revokes_refresh_token(self, client, admin_tokens):
        """FIX VULN-015: Providing refresh_token in logout body revokes it too."""
        access_token = admin_tokens["access_token"]
        refresh_token = admin_tokens["refresh_token"]

        r = client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers=auth_header(access_token),
        )
        assert r.status_code == 200

        # Refresh token must now be revoked
        r2 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert r2.status_code == 401


class TestTokenExpiry:
    """Token expiry and purge edge cases."""

    def test_expired_token_returns_401(self, client):
        """An expired JWT access token is rejected with 401."""
        expired_token = pyjwt.encode(
            {
                "sub": "user_admin_001",
                "email": "admin@test.com",
                "role": "ADMIN",
                "jti": "test-expired-jti",
                "type": "access",
                "iat": int(time.time()) - 7200,
                "exp": int(time.time()) - 3600,
            },
            "test-secret-key-for-testing-only",
            algorithm="HS256",
        )
        r = client.get("/resources", headers=auth_header(expired_token))
        assert r.status_code == 401

    def test_purge_removes_expired_revoked_tokens(self):
        """FIX VULN-005: purge_expired_tokens removes entries whose expiry has passed."""
        from src.data import store as data_store
        from src.domain.auth_service import purge_expired_tokens

        data_store.revoked_tokens["expired-jti"] = time.time() - 1
        data_store.revoked_tokens["valid-jti"] = time.time() + 3600

        purge_expired_tokens()

        assert "expired-jti" not in data_store.revoked_tokens
        assert "valid-jti" in data_store.revoked_tokens

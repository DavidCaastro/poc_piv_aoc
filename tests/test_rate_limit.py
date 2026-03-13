"""Tests for rate limiting.

Covers RF-07 and RF-10 scenarios.
"""

import pytest
from tests.conftest import auth_header


class TestRateLimiting:
    """RF-07: Rate limiting per role."""

    def test_viewer_rate_limit_exceeded(self, client, viewer_token):
        """RF-10 scenario: VIEWER enviando > 10 req/min -> 429."""
        headers = auth_header(viewer_token)

        # First 10 requests should succeed
        for i in range(10):
            r = client.get("/resources", headers=headers)
            assert r.status_code == 200, f"Request {i+1} should succeed"

        # 11th request should be rate limited
        r = client.get("/resources", headers=headers)
        assert r.status_code == 429
        assert r.json()["detail"] == "Limite de solicitudes excedido."

    def test_editor_higher_limit(self, client, editor_token):
        """EDITOR has higher rate limit (30 req/min)."""
        headers = auth_header(editor_token)

        # First 10 requests succeed (VIEWER limit)
        for i in range(10):
            r = client.get("/resources", headers=headers)
            assert r.status_code == 200

        # 11th request still succeeds for EDITOR
        r = client.get("/resources", headers=headers)
        assert r.status_code == 200

    def test_admin_highest_limit(self, client, admin_token):
        """ADMIN has highest rate limit (100 req/min) — verified beyond EDITOR limit."""
        headers = auth_header(admin_token)

        # 31 requests all succeed (beyond EDITOR limit of 30)
        for i in range(31):
            r = client.get("/resources", headers=headers)
            assert r.status_code == 200

    def test_admin_rate_limit_exceeded_at_100(self, client, admin_token):
        """RF-07: ADMIN rate limit is exactly 100 req/min — 101st request is 429."""
        headers = auth_header(admin_token)

        for i in range(100):
            r = client.get("/resources", headers=headers)
            assert r.status_code == 200, f"Request {i + 1} should succeed"

        r = client.get("/resources", headers=headers)
        assert r.status_code == 429
        assert r.json()["detail"] == "Limite de solicitudes excedido."

    def test_editor_rate_limit_exceeded_at_30(self, client, editor_token):
        """RF-07: EDITOR rate limit is exactly 30 req/min — 31st request is 429."""
        headers = auth_header(editor_token)

        for i in range(30):
            r = client.get("/resources", headers=headers)
            assert r.status_code == 200, f"Request {i + 1} should succeed"

        r = client.get("/resources", headers=headers)
        assert r.status_code == 429

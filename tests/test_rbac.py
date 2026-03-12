"""Tests for RBAC: privilege escalation scenarios.

Covers RF-05, RF-06, and RF-10 scenarios.
"""

import pytest
from tests.conftest import auth_header


class TestPrivilegeEscalation:
    """RF-10: Privilege escalation tests."""

    def test_viewer_cannot_access_admin_endpoint(self, client, viewer_token):
        """RF-10 scenario: VIEWER intentando endpoint de ADMIN -> 403."""
        r = client.get("/admin/audit-log", headers=auth_header(viewer_token))
        assert r.status_code == 403
        assert r.json()["detail"] == "Permisos insuficientes."

    def test_viewer_cannot_post_resources(self, client, viewer_token):
        """VIEWER cannot create resources."""
        r = client.post("/resources", json={"title": "Test"},
                       headers=auth_header(viewer_token))
        assert r.status_code == 403

    def test_viewer_cannot_put_resources(self, client, viewer_token, admin_token):
        """VIEWER cannot update resources."""
        # Create a resource as admin first
        client.post("/resources", json={"title": "Test"},
                   headers=auth_header(admin_token))
        r = client.put("/resources/1", json={"title": "Updated"},
                      headers=auth_header(viewer_token))
        assert r.status_code == 403

    def test_viewer_cannot_delete_resources(self, client, viewer_token, admin_token):
        """VIEWER cannot delete resources."""
        client.post("/resources", json={"title": "Test"},
                   headers=auth_header(admin_token))
        r = client.delete("/resources/1", headers=auth_header(viewer_token))
        assert r.status_code == 403

    def test_editor_cannot_delete_resources(self, client, editor_token, admin_token):
        """RF-10 scenario: EDITOR intentando DELETE -> 403."""
        client.post("/resources", json={"title": "Test"},
                   headers=auth_header(admin_token))
        r = client.delete("/resources/1", headers=auth_header(editor_token))
        assert r.status_code == 403

    def test_editor_cannot_access_audit_log(self, client, editor_token):
        """EDITOR cannot view audit log."""
        r = client.get("/admin/audit-log", headers=auth_header(editor_token))
        assert r.status_code == 403


class TestRolePermissions:
    """RF-05, RF-06: Role-based access works correctly."""

    def test_viewer_can_get_resources(self, client, viewer_token):
        r = client.get("/resources", headers=auth_header(viewer_token))
        assert r.status_code == 200

    def test_editor_can_create_resources(self, client, editor_token):
        r = client.post("/resources", json={"title": "Test"},
                       headers=auth_header(editor_token))
        assert r.status_code == 201

    def test_editor_can_update_resources(self, client, editor_token):
        # Create first
        client.post("/resources", json={"title": "Test"},
                   headers=auth_header(editor_token))
        r = client.put("/resources/1", json={"title": "Updated"},
                      headers=auth_header(editor_token))
        assert r.status_code == 200

    def test_admin_can_delete_resources(self, client, admin_token):
        client.post("/resources", json={"title": "Test"},
                   headers=auth_header(admin_token))
        r = client.delete("/resources/1", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_admin_can_view_audit_log(self, client, admin_token):
        r = client.get("/admin/audit-log", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_no_auth_returns_401(self, client):
        """Accessing protected endpoint without token returns 401."""
        r = client.get("/resources")
        assert r.status_code == 401

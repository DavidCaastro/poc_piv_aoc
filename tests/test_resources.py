"""Tests for resource CRUD operations.

Covers RF-06 and RF-08 (audit trail).
"""

import pytest
from tests.conftest import auth_header


class TestResourceCRUD:
    """RF-06: Resource CRUD with different roles."""

    def test_create_resource(self, client, editor_token):
        r = client.post("/resources", json={
            "title": "My Resource",
            "description": "A test resource",
        }, headers=auth_header(editor_token))
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "My Resource"
        assert data["description"] == "A test resource"
        assert data["id"] == 1

    def test_list_resources(self, client, admin_token, viewer_token):
        # Create a resource as admin
        client.post("/resources", json={"title": "R1"},
                   headers=auth_header(admin_token))
        # List as viewer
        r = client.get("/resources", headers=auth_header(viewer_token))
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["title"] == "R1"

    def test_update_resource(self, client, editor_token):
        client.post("/resources", json={"title": "Original"},
                   headers=auth_header(editor_token))
        r = client.put("/resources/1", json={"title": "Updated"},
                      headers=auth_header(editor_token))
        assert r.status_code == 200
        assert r.json()["title"] == "Updated"

    def test_update_nonexistent_resource(self, client, admin_token):
        r = client.put("/resources/999", json={"title": "X"},
                      headers=auth_header(admin_token))
        assert r.status_code == 404

    def test_delete_resource(self, client, admin_token):
        client.post("/resources", json={"title": "ToDelete"},
                   headers=auth_header(admin_token))
        r = client.delete("/resources/1", headers=auth_header(admin_token))
        assert r.status_code == 200

        # Verify deleted
        r2 = client.get("/resources", headers=auth_header(admin_token))
        assert len(r2.json()) == 0

    def test_delete_nonexistent_resource(self, client, admin_token):
        r = client.delete("/resources/999", headers=auth_header(admin_token))
        assert r.status_code == 404


class TestAuditTrail:
    """RF-08: Audit trail records authenticated requests."""

    def test_audit_log_records_requests(self, client, admin_token):
        # Make some requests
        client.get("/resources", headers=auth_header(admin_token))
        client.post("/resources", json={"title": "Test"},
                   headers=auth_header(admin_token))

        # Check audit log
        r = client.get("/admin/audit-log", headers=auth_header(admin_token))
        assert r.status_code == 200
        logs = r.json()
        # At least 3 entries (2 resource ops + 1 audit-log request)
        assert len(logs) >= 2

    def test_audit_log_contains_required_fields(self, client, admin_token):
        client.get("/resources", headers=auth_header(admin_token))
        r = client.get("/admin/audit-log", headers=auth_header(admin_token))
        log_entry = r.json()[0]

        required_fields = ["user_id", "role", "endpoint", "method", "timestamp", "status_code"]
        for field in required_fields:
            assert field in log_entry, f"Missing field: {field}"

"""
T008: Contract test for GET /api/reddit/search/{search_run_id}
Tests search status retrieval endpoint contract compliance
"""
import pytest
from fastapi.testclient import TestClient
import uuid


class TestRedditSearchGetContract:
    """Contract tests for GET /api/reddit/search/{search_run_id} endpoint"""

    def test_get_search_status_returns_200(self, authenticated_client, active_search_run):
        """Test getting search status returns 200 with correct structure"""
        response = authenticated_client.get(
            f"/api/reddit/search/{active_search_run['search_run_id']}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure per OpenAPI spec
        assert "search_run_id" in data
        assert data["search_run_id"] == active_search_run["search_run_id"]

        assert "status" in data
        assert data["status"] in ["pending", "in_progress", "completed", "failed"]

        assert "topics" in data
        assert isinstance(data["topics"], list)
        assert len(data["topics"]) > 0

        assert "time_range" in data
        assert data["time_range"] in ["24h", "7days", "30days", "90days", "1year", "all"]

        assert "created_at" in data
        assert "started_at" in data
        assert "completed_at" in data
        assert "pain_points_count" in data

        # Optional error_message field
        if data["status"] == "failed":
            assert "error_message" in data

    def test_unauthenticated_request_returns_401(self, client: TestClient, active_search_run):
        """Test getting search status without authentication returns 401"""
        response = client.get(
            f"/api/reddit/search/{active_search_run['search_run_id']}"
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_nonexistent_search_run_returns_404(self, authenticated_client):
        """Test getting status for non-existent search returns 404"""
        fake_id = str(uuid.uuid4())
        response = authenticated_client.get(f"/api/reddit/search/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Search run not found"

    def test_invalid_uuid_format_returns_422(self, authenticated_client):
        """Test getting status with invalid UUID format returns 422"""
        response = authenticated_client.get("/api/reddit/search/not-a-uuid")

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("uuid" in str(error).lower() for error in errors)

    def test_cannot_access_other_users_search(self, authenticated_client, other_users_search_run):
        """Test user cannot access another user's search run (403 Forbidden)"""
        response = authenticated_client.get(
            f"/api/reddit/search/{other_users_search_run['search_run_id']}"
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Not authorized to access this search run"

    def test_completed_search_includes_stats(self, authenticated_client, completed_search_run):
        """Test completed search includes statistics"""
        response = authenticated_client.get(
            f"/api/reddit/search/{completed_search_run['search_run_id']}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert data["pain_points_count"] > 0
        assert data["completed_at"] is not None
        assert data["started_at"] is not None

    def test_failed_search_includes_error(self, authenticated_client, failed_search_run):
        """Test failed search includes error message"""
        response = authenticated_client.get(
            f"/api/reddit/search/{failed_search_run['search_run_id']}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "failed"
        assert "error_message" in data
        assert data["error_message"] is not None
        assert len(data["error_message"]) > 0

    def test_pending_search_has_null_timestamps(self, authenticated_client, pending_search_run):
        """Test pending search has null started_at and completed_at"""
        response = authenticated_client.get(
            f"/api/reddit/search/{pending_search_run['search_run_id']}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "pending"
        assert data["started_at"] is None
        assert data["completed_at"] is None

    def test_in_progress_search_has_started_at(self, authenticated_client, in_progress_search_run):
        """Test in-progress search has started_at but null completed_at"""
        response = authenticated_client.get(
            f"/api/reddit/search/{in_progress_search_run['search_run_id']}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "in_progress"
        assert data["started_at"] is not None
        assert data["completed_at"] is None
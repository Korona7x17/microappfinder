"""
T009: Contract test for GET /api/reddit/search/{search_run_id}/results
Tests search results retrieval endpoint contract compliance
"""
import pytest
from fastapi.testclient import TestClient
import uuid


class TestRedditSearchResultsContract:
    """Contract tests for GET /api/reddit/search/{search_run_id}/results endpoint"""

    def test_get_completed_search_results_returns_200(self, authenticated_client, completed_search_with_results):
        """Test getting results for completed search returns 200 with pain points"""
        response = authenticated_client.get(
            f"/api/reddit/search/{completed_search_with_results['search_run_id']}/results"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure per OpenAPI spec
        assert "search_run_id" in data
        assert data["search_run_id"] == completed_search_with_results["search_run_id"]

        assert "status" in data
        assert data["status"] == "completed"

        assert "pain_points" in data
        assert isinstance(data["pain_points"], list)
        assert len(data["pain_points"]) > 0

        # Verify pain point structure
        pain_point = data["pain_points"][0]
        assert "id" in pain_point
        assert "extracted_text" in pain_point
        assert "relevance_score" in pain_point
        assert "sentiment_score" in pain_point
        assert "source_reddit_post_ids" in pain_point
        assert "source_deleted" in pain_point
        assert "created_at" in pain_point

        # Verify data types and ranges
        assert isinstance(pain_point["extracted_text"], str)
        assert len(pain_point["extracted_text"]) <= 500
        assert 0 <= pain_point["relevance_score"] <= 1
        assert -1 <= pain_point["sentiment_score"] <= 1
        assert isinstance(pain_point["source_reddit_post_ids"], list)
        assert isinstance(pain_point["source_deleted"], bool)

    def test_results_sorted_by_relevance_score(self, authenticated_client, completed_search_with_results):
        """Test that pain points are sorted by relevance_score descending"""
        response = authenticated_client.get(
            f"/api/reddit/search/{completed_search_with_results['search_run_id']}/results"
        )

        assert response.status_code == 200
        pain_points = response.json()["pain_points"]

        # Verify descending order
        for i in range(len(pain_points) - 1):
            assert pain_points[i]["relevance_score"] >= pain_points[i + 1]["relevance_score"]

    def test_unauthenticated_request_returns_401(self, client: TestClient, completed_search_with_results):
        """Test getting results without authentication returns 401"""
        response = client.get(
            f"/api/reddit/search/{completed_search_with_results['search_run_id']}/results"
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_nonexistent_search_run_returns_404(self, authenticated_client):
        """Test getting results for non-existent search returns 404"""
        fake_id = str(uuid.uuid4())
        response = authenticated_client.get(f"/api/reddit/search/{fake_id}/results")

        assert response.status_code == 404
        assert response.json()["detail"] == "Search run not found"

    def test_cannot_access_other_users_results(self, authenticated_client, other_users_completed_search):
        """Test user cannot access another user's search results (403 Forbidden)"""
        response = authenticated_client.get(
            f"/api/reddit/search/{other_users_completed_search['search_run_id']}/results"
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Not authorized to access this search run"

    def test_pending_search_returns_202(self, authenticated_client, pending_search_run):
        """Test getting results for pending search returns 202 Accepted"""
        response = authenticated_client.get(
            f"/api/reddit/search/{pending_search_run['search_run_id']}/results"
        )

        assert response.status_code == 202
        data = response.json()

        assert "status" in data
        assert data["status"] == "pending"
        assert "message" in data
        assert "not started" in data["message"].lower()

    def test_in_progress_search_returns_202(self, authenticated_client, in_progress_search_run):
        """Test getting results for in-progress search returns 202 Accepted"""
        response = authenticated_client.get(
            f"/api/reddit/search/{in_progress_search_run['search_run_id']}/results"
        )

        assert response.status_code == 202
        data = response.json()

        assert "status" in data
        assert data["status"] == "in_progress"
        assert "message" in data
        assert "processing" in data["message"].lower()

    def test_failed_search_returns_500(self, authenticated_client, failed_search_run):
        """Test getting results for failed search returns 500 with error"""
        response = authenticated_client.get(
            f"/api/reddit/search/{failed_search_run['search_run_id']}/results"
        )

        assert response.status_code == 500
        data = response.json()

        assert "status" in data
        assert data["status"] == "failed"
        assert "error_message" in data
        assert len(data["error_message"]) > 0

    def test_empty_results_returns_200_with_empty_array(self, authenticated_client, completed_search_no_results):
        """Test completed search with no results returns 200 with empty array"""
        response = authenticated_client.get(
            f"/api/reddit/search/{completed_search_no_results['search_run_id']}/results"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert "pain_points" in data
        assert isinstance(data["pain_points"], list)
        assert len(data["pain_points"]) == 0

    def test_pagination_parameters(self, authenticated_client, completed_search_many_results):
        """Test pagination parameters limit and offset"""
        # Get first 10 results
        response = authenticated_client.get(
            f"/api/reddit/search/{completed_search_many_results['search_run_id']}/results?limit=10&offset=0"
        )
        assert response.status_code == 200
        first_page = response.json()["pain_points"]
        assert len(first_page) <= 10

        # Get next 10 results
        response = authenticated_client.get(
            f"/api/reddit/search/{completed_search_many_results['search_run_id']}/results?limit=10&offset=10"
        )
        assert response.status_code == 200
        second_page = response.json()["pain_points"]

        # Ensure no overlap
        first_ids = {p["id"] for p in first_page}
        second_ids = {p["id"] for p in second_page}
        assert len(first_ids & second_ids) == 0  # No intersection
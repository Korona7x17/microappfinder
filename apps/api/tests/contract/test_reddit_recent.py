"""
T010: Contract test for GET /api/reddit/recent
Tests recent pain points retrieval endpoint contract compliance
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


class TestRedditRecentContract:
    """Contract tests for GET /api/reddit/recent endpoint"""

    def test_get_recent_pain_points_returns_200(self, authenticated_client, recent_pain_points_data):
        """Test getting recent pain points returns 200 with correct structure"""
        response = authenticated_client.get("/api/reddit/recent")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure per OpenAPI spec
        assert "pain_points" in data
        assert isinstance(data["pain_points"], list)
        assert len(data["pain_points"]) <= 20  # Max 20 as per spec

        # Verify pain point structure if any exist
        if len(data["pain_points"]) > 0:
            pain_point = data["pain_points"][0]
            assert "id" in pain_point
            assert "extracted_text" in pain_point
            assert "relevance_score" in pain_point
            assert "sentiment_score" in pain_point
            assert "created_at" in pain_point
            assert "topics" in pain_point  # Associated topics from search run

            # Verify data types and ranges
            assert isinstance(pain_point["extracted_text"], str)
            assert len(pain_point["extracted_text"]) <= 500
            assert 0 <= pain_point["relevance_score"] <= 1
            assert -1 <= pain_point["sentiment_score"] <= 1
            assert isinstance(pain_point["topics"], list)

    def test_results_sorted_by_relevance_score(self, authenticated_client, recent_pain_points_data):
        """Test that recent pain points are sorted by relevance_score descending"""
        response = authenticated_client.get("/api/reddit/recent")

        assert response.status_code == 200
        pain_points = response.json()["pain_points"]

        # Verify descending order if multiple points exist
        for i in range(len(pain_points) - 1):
            assert pain_points[i]["relevance_score"] >= pain_points[i + 1]["relevance_score"]

    def test_only_last_7_days_included(self, authenticated_client, db_session):
        """Test that only pain points from last 7 days are included"""
        response = authenticated_client.get("/api/reddit/recent")

        assert response.status_code == 200
        pain_points = response.json()["pain_points"]

        # Verify all pain points are within last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        for pain_point in pain_points:
            created_at = datetime.fromisoformat(pain_point["created_at"].replace("Z", "+00:00"))
            assert created_at >= seven_days_ago

    def test_unauthenticated_request_returns_401(self, client: TestClient):
        """Test getting recent pain points without authentication returns 401"""
        response = client.get("/api/reddit/recent")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_empty_database_returns_fallback_message(self, authenticated_client, empty_database):
        """Test empty database returns helpful fallback message"""
        response = authenticated_client.get("/api/reddit/recent")

        assert response.status_code == 200
        data = response.json()

        assert "pain_points" in data
        assert isinstance(data["pain_points"], list)
        assert len(data["pain_points"]) == 0

        # Should include a helpful message
        assert "message" in data
        assert "no recent" in data["message"].lower() or "start a search" in data["message"].lower()

    def test_excludes_deleted_sources(self, authenticated_client, pain_points_with_deleted):
        """Test that pain points with source_deleted=true are excluded"""
        response = authenticated_client.get("/api/reddit/recent")

        assert response.status_code == 200
        pain_points = response.json()["pain_points"]

        # Verify no pain points have source_deleted=true
        for pain_point in pain_points:
            # Note: source_deleted might not be included in response if false
            if "source_deleted" in pain_point:
                assert pain_point["source_deleted"] is False

    def test_max_20_results_returned(self, authenticated_client, many_recent_pain_points):
        """Test that maximum 20 results are returned even if more exist"""
        response = authenticated_client.get("/api/reddit/recent")

        assert response.status_code == 200
        pain_points = response.json()["pain_points"]

        assert len(pain_points) == 20  # Exactly 20, not more

    def test_aggregates_from_all_users_searches(self, authenticated_client, multi_user_pain_points):
        """Test that recent endpoint shows pain points from all users (not just current user)"""
        response = authenticated_client.get("/api/reddit/recent")

        assert response.status_code == 200
        pain_points = response.json()["pain_points"]

        # Should include pain points from multiple users' search runs
        # (This is the fallback/discovery behavior)
        assert len(pain_points) > 0

        # Verify we're not seeing user-specific data
        for pain_point in pain_points:
            assert "user_id" not in pain_point  # User data should not be exposed

    def test_includes_nsfw_filter_parameter(self, authenticated_client, nsfw_pain_points):
        """Test that NSFW filter parameter works"""
        # Get without NSFW filter (default excludes NSFW)
        response = authenticated_client.get("/api/reddit/recent")
        assert response.status_code == 200
        default_points = response.json()["pain_points"]

        # Verify no NSFW content by default
        for point in default_points:
            assert not point.get("is_nsfw", False)

        # Get with NSFW included
        response = authenticated_client.get("/api/reddit/recent?include_nsfw=true")
        assert response.status_code == 200
        all_points = response.json()["pain_points"]

        # Should have more results when NSFW included
        assert len(all_points) >= len(default_points)
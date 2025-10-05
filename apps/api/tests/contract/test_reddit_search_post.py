"""
T007: Contract test for POST /api/reddit/search
Tests Reddit search initiation endpoint contract compliance
"""
import pytest
from fastapi.testclient import TestClient
import uuid


class TestRedditSearchPostContract:
    """Contract tests for POST /api/reddit/search endpoint"""

    def test_successful_search_initiation_returns_201(self, authenticated_client):
        """Test successful search initiation returns 201 with search_run_id"""
        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["productivity tools", "time management"],
                "time_range": "7days"
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure per OpenAPI spec
        assert "search_run_id" in data
        assert isinstance(data["search_run_id"], str)
        assert len(data["search_run_id"]) == 36  # UUID format

        assert "status" in data
        assert data["status"] in ["pending", "in_progress"]

        assert "message" in data
        assert "started" in data["message"].lower()

    def test_unauthenticated_request_returns_401(self, client: TestClient):
        """Test search without authentication returns 401"""
        response = client.post(
            "/api/reddit/search",
            json={
                "topics": ["productivity"],
                "time_range": "24h"
            }
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_invalid_time_range_returns_422(self, authenticated_client):
        """Test search with invalid time_range returns 422"""
        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["productivity"],
                "time_range": "invalid_range"
            }
        )

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("time_range" in str(error).lower() for error in errors)

    def test_valid_time_ranges(self, authenticated_client):
        """Test all valid time_range values are accepted"""
        valid_ranges = ["24h", "7days", "30days", "90days", "1year", "all"]

        for time_range in valid_ranges:
            response = authenticated_client.post(
                "/api/reddit/search",
                json={
                    "topics": [f"test_{uuid.uuid4()}"],
                    "time_range": time_range
                }
            )
            assert response.status_code == 201, f"time_range '{time_range}' should be valid"

    def test_empty_topics_array_returns_422(self, authenticated_client):
        """Test search with empty topics array returns 422"""
        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": [],
                "time_range": "7days"
            }
        )

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("topics" in str(error).lower() for error in errors)

    def test_too_many_topics_returns_422(self, authenticated_client):
        """Test search with more than 5 topics returns 422"""
        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["topic1", "topic2", "topic3", "topic4", "topic5", "topic6"],
                "time_range": "7days"
            }
        )

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("topics" in str(error).lower() and "5" in str(error) for error in errors)

    def test_topic_validation(self, authenticated_client):
        """Test topic keyword validation (2-100 chars, alphanumeric + spaces)"""
        # Too short
        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["a"],  # Only 1 char
                "time_range": "7days"
            }
        )
        assert response.status_code == 422

        # Too long
        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["x" * 101],  # 101 chars
                "time_range": "7days"
            }
        )
        assert response.status_code == 422

        # Invalid characters
        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["test@#$%"],  # Special chars not allowed
                "time_range": "7days"
            }
        )
        assert response.status_code == 422

    def test_missing_required_fields_returns_422(self, authenticated_client):
        """Test search with missing required fields returns 422"""
        # Missing topics
        response = authenticated_client.post(
            "/api/reddit/search",
            json={"time_range": "7days"}
        )
        assert response.status_code == 422

        # Missing time_range
        response = authenticated_client.post(
            "/api/reddit/search",
            json={"topics": ["productivity"]}
        )
        assert response.status_code == 422

        # Empty body
        response = authenticated_client.post("/api/reddit/search", json={})
        assert response.status_code == 422

    def test_search_creates_database_records(self, authenticated_client, db_session):
        """Test that search creates SearchRun and Topic records in database"""
        topic_keyword = f"unique_topic_{uuid.uuid4()}"

        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": [topic_keyword],
                "time_range": "24h"
            }
        )

        assert response.status_code == 201
        search_run_id = response.json()["search_run_id"]

        # Verify SearchRun was created
        from app.models.search_run import SearchRun
        search_run = db_session.query(SearchRun).filter_by(id=search_run_id).first()
        assert search_run is not None
        assert search_run.status in ["pending", "in_progress"]
        assert search_run.time_range == "24h"

        # Verify Topic was created/reused
        from app.models.topic import Topic
        topic = db_session.query(Topic).filter_by(keyword=topic_keyword).first()
        assert topic is not None

    def test_concurrent_searches_allowed(self, authenticated_client):
        """Test that users can have multiple concurrent searches"""
        # Start first search
        response1 = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["topic1"],
                "time_range": "24h"
            }
        )
        assert response1.status_code == 201

        # Start second search immediately
        response2 = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["topic2"],
                "time_range": "7days"
            }
        )
        assert response2.status_code == 201

        # Both should have different IDs
        assert response1.json()["search_run_id"] != response2.json()["search_run_id"]
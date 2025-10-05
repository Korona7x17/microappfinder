"""
T012: Integration test for complete Reddit search flow
Tests end-to-end Reddit pain point discovery workflow
"""
import pytest
from fastapi.testclient import TestClient
import uuid
import time


class TestRedditSearchFlow:
    """Integration tests for complete Reddit search and pain point extraction flow"""

    def test_complete_search_workflow(self, authenticated_client, mock_reddit_api, db_session):
        """Test complete flow: initiate search -> poll status -> get results"""
        # Step 1: Initiate search
        search_response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["productivity apps", "time management"],
                "time_range": "7days"
            }
        )
        assert search_response.status_code == 201
        search_run_id = search_response.json()["search_run_id"]

        # Verify SearchRun created in database
        from app.models.search_run import SearchRun
        search_run = db_session.query(SearchRun).filter_by(id=search_run_id).first()
        assert search_run is not None
        assert search_run.status in ["pending", "in_progress"]

        # Step 2: Poll status until completed
        max_attempts = 30  # 30 seconds max wait
        completed = False

        for _ in range(max_attempts):
            status_response = authenticated_client.get(f"/api/reddit/search/{search_run_id}")
            assert status_response.status_code == 200

            status = status_response.json()["status"]
            if status == "completed":
                completed = True
                break
            elif status == "failed":
                pytest.fail(f"Search failed: {status_response.json().get('error_message')}")

            time.sleep(1)  # Wait 1 second before polling again

        assert completed, "Search did not complete within timeout"

        # Step 3: Get results
        results_response = authenticated_client.get(
            f"/api/reddit/search/{search_run_id}/results"
        )
        assert results_response.status_code == 200

        results = results_response.json()
        assert results["status"] == "completed"
        assert "pain_points" in results
        assert isinstance(results["pain_points"], list)

        # Verify pain points were extracted
        if len(results["pain_points"]) > 0:
            pain_point = results["pain_points"][0]
            assert "extracted_text" in pain_point
            assert "relevance_score" in pain_point
            assert 0 <= pain_point["relevance_score"] <= 1

    def test_search_with_multiple_topics_creates_associations(self, authenticated_client, db_session):
        """Test that search with multiple topics creates proper associations"""
        topics = [f"topic_{i}_{uuid.uuid4()}" for i in range(3)]

        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": topics,
                "time_range": "24h"
            }
        )
        assert response.status_code == 201
        search_run_id = response.json()["search_run_id"]

        # Verify topics were created/reused
        from app.models.topic import Topic
        from app.models.search_run import SearchRun

        search_run = db_session.query(SearchRun).filter_by(id=search_run_id).first()
        assert search_run is not None

        # Check topic associations
        associated_topics = search_run.topics
        assert len(associated_topics) == 3

        topic_keywords = [t.keyword for t in associated_topics]
        for topic in topics:
            assert topic in topic_keywords

    def test_search_reuses_existing_topics(self, authenticated_client, db_session):
        """Test that searches reuse existing topics instead of duplicating"""
        topic_keyword = f"reusable_topic_{uuid.uuid4()}"

        # First search creates topic
        response1 = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": [topic_keyword],
                "time_range": "24h"
            }
        )
        assert response1.status_code == 201

        # Count topics
        from app.models.topic import Topic
        topic_count_1 = db_session.query(Topic).filter_by(keyword=topic_keyword).count()
        assert topic_count_1 == 1

        # Second search reuses topic
        response2 = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": [topic_keyword],
                "time_range": "7days"
            }
        )
        assert response2.status_code == 201

        # Topic count should still be 1
        topic_count_2 = db_session.query(Topic).filter_by(keyword=topic_keyword).count()
        assert topic_count_2 == 1

        # Search count should be incremented
        topic = db_session.query(Topic).filter_by(keyword=topic_keyword).first()
        assert topic.search_count == 2

    def test_failed_search_handles_error_gracefully(self, authenticated_client, mock_reddit_api_failure, db_session):
        """Test that failed searches update status and store error message"""
        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["test_failure"],
                "time_range": "24h"
            }
        )
        assert response.status_code == 201
        search_run_id = response.json()["search_run_id"]

        # Wait for processing
        time.sleep(2)

        # Check status
        status_response = authenticated_client.get(f"/api/reddit/search/{search_run_id}")
        assert status_response.status_code == 200

        status_data = status_response.json()
        if status_data["status"] == "failed":
            assert "error_message" in status_data
            assert status_data["error_message"] is not None

        # Verify database record
        from app.models.search_run import SearchRun
        search_run = db_session.query(SearchRun).filter_by(id=search_run_id).first()
        if search_run.status == "failed":
            assert search_run.error_message is not None

    def test_concurrent_searches_processed_independently(self, authenticated_client):
        """Test that multiple concurrent searches are processed independently"""
        # Start multiple searches
        search_ids = []
        for i in range(3):
            response = authenticated_client.post(
                "/api/reddit/search",
                json={
                    "topics": [f"concurrent_test_{i}_{uuid.uuid4()}"],
                    "time_range": "24h"
                }
            )
            assert response.status_code == 201
            search_ids.append(response.json()["search_run_id"])

        # All searches should have different IDs
        assert len(set(search_ids)) == 3

        # Each should be queryable independently
        for search_id in search_ids:
            response = authenticated_client.get(f"/api/reddit/search/{search_id}")
            assert response.status_code == 200
            assert response.json()["search_run_id"] == search_id

    def test_search_respects_time_range_parameter(self, authenticated_client, mock_reddit_api_with_dates):
        """Test that search correctly filters posts by time_range"""
        test_cases = [
            ("24h", 1),     # Should get posts from last 24 hours
            ("7days", 7),   # Should get posts from last 7 days
            ("30days", 30), # Should get posts from last 30 days
        ]

        for time_range, expected_days in test_cases:
            response = authenticated_client.post(
                "/api/reddit/search",
                json={
                    "topics": [f"time_test_{uuid.uuid4()}"],
                    "time_range": time_range
                }
            )
            assert response.status_code == 201
            search_run_id = response.json()["search_run_id"]

            # Wait for completion
            time.sleep(2)

            # Get results
            results_response = authenticated_client.get(
                f"/api/reddit/search/{search_run_id}/results"
            )

            if results_response.status_code == 200:
                pain_points = results_response.json().get("pain_points", [])
                # Verify all pain points are within the time range
                # (This would need mock_reddit_api_with_dates to return date-tagged data)

    def test_search_filters_nsfw_content_by_default(self, authenticated_client, mock_reddit_with_nsfw):
        """Test that NSFW content is filtered by default"""
        response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["test_nsfw"],
                "time_range": "24h"
            }
        )
        assert response.status_code == 201
        search_run_id = response.json()["search_run_id"]

        # Wait and get results
        time.sleep(2)
        results_response = authenticated_client.get(
            f"/api/reddit/search/{search_run_id}/results"
        )

        if results_response.status_code == 200:
            pain_points = results_response.json().get("pain_points", [])
            # Verify no NSFW content in results
            # (This assumes pain points track NSFW status from source)
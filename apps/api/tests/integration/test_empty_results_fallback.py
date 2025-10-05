"""
T014: Integration test for empty results fallback behavior
Tests fallback behavior when searches return no results
"""
import pytest
from fastapi.testclient import TestClient
import uuid
import time
from datetime import datetime, timedelta


class TestEmptyResultsFallback:
    """Integration tests for empty results fallback behavior"""

    def test_empty_search_shows_recent_pain_points_fallback(self, authenticated_client, existing_pain_points, mock_empty_reddit):
        """Test that empty search results show recent pain points as fallback"""
        # Initiate a search that will return no results
        search_response = authenticated_client.post(
            "/api/reddit/search",
            json={
                "topics": ["extremely_specific_nonexistent_topic_xyz123"],
                "time_range": "24h"
            }
        )
        assert search_response.status_code == 201
        search_run_id = search_response.json()["search_run_id"]

        # Wait for search to complete
        max_attempts = 10
        for _ in range(max_attempts):
            status = authenticated_client.get(f"/api/reddit/search/{search_run_id}")
            if status.json()["status"] == "completed":
                break
            time.sleep(1)

        # Get results - should be empty
        results_response = authenticated_client.get(
            f"/api/reddit/search/{search_run_id}/results"
        )
        assert results_response.status_code == 200

        results = results_response.json()
        assert results["status"] == "completed"
        assert len(results["pain_points"]) == 0

        # Check if fallback message/data is provided
        assert "message" in results or "fallback" in results or "suggestions" in results

        # Recent endpoint should show existing pain points as discovery
        recent_response = authenticated_client.get("/api/reddit/recent")
        assert recent_response.status_code == 200

        recent_data = recent_response.json()
        assert len(recent_data["pain_points"]) > 0  # Should show existing data

    def test_new_user_sees_recent_pain_points(self, client: TestClient, existing_pain_points):
        """Test that new users see recent pain points for discovery"""
        # Register new user
        email = f"new_user_{uuid.uuid4()}@example.com"
        password = "SecurePassword123"

        client.post("/api/auth/register", json={"email": email, "password": password})
        login = client.post("/api/auth/login", json={"email": email, "password": password})
        client.cookies.set("access_token", login.cookies.get("access_token"))

        # New user with no searches should see recent pain points
        response = client.get("/api/reddit/recent")
        assert response.status_code == 200

        data = response.json()
        assert "pain_points" in data

        # Should see top 20 recent pain points from all users
        if len(existing_pain_points) > 0:
            assert len(data["pain_points"]) > 0
            assert len(data["pain_points"]) <= 20

            # Verify they're sorted by relevance
            scores = [p["relevance_score"] for p in data["pain_points"]]
            assert scores == sorted(scores, reverse=True)

    def test_empty_database_shows_helpful_message(self, authenticated_client, empty_database):
        """Test that completely empty database shows helpful onboarding message"""
        # Recent endpoint with no data
        response = authenticated_client.get("/api/reddit/recent")
        assert response.status_code == 200

        data = response.json()
        assert "pain_points" in data
        assert len(data["pain_points"]) == 0

        # Should include helpful message
        assert "message" in data
        assert any(word in data["message"].lower() for word in ["no", "start", "search", "empty"])

        # Starting a search should work
        search = authenticated_client.post(
            "/api/reddit/search",
            json={"topics": ["startup ideas"], "time_range": "7days"}
        )
        assert search.status_code == 201

    def test_fallback_excludes_deleted_sources(self, authenticated_client, db_session):
        """Test that fallback results exclude pain points with deleted sources"""
        from app.models.user import User
        from app.models.search_run import SearchRun
        from app.models.pain_point import PainPoint
        import uuid as uuid_lib

        # Create test data with mix of deleted and active sources
        user = db_session.query(User).first()
        if not user:
            user = User(
                id=str(uuid_lib.uuid4()),
                email=f"test_{uuid.uuid4()}@example.com",
                hashed_password="hashed"
            )
            db_session.add(user)
            db_session.commit()

        search_run = SearchRun(
            id=str(uuid_lib.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="24h"
        )
        db_session.add(search_run)
        db_session.commit()

        # Add pain points with different source_deleted status
        pain_points = [
            PainPoint(
                id=str(uuid_lib.uuid4()),
                search_run_id=search_run.id,
                extracted_text=f"Active pain point {i}",
                relevance_score=0.9 - (i * 0.1),
                sentiment_score=0.0,
                source_reddit_post_ids=["post1", "post2"],
                source_deleted=False
            ) for i in range(3)
        ]

        deleted_points = [
            PainPoint(
                id=str(uuid_lib.uuid4()),
                search_run_id=search_run.id,
                extracted_text=f"Deleted source pain point {i}",
                relevance_score=0.95,  # High score but deleted
                sentiment_score=0.0,
                source_reddit_post_ids=["deleted1"],
                source_deleted=True
            ) for i in range(2)
        ]

        db_session.add_all(pain_points + deleted_points)
        db_session.commit()

        # Get recent pain points
        response = authenticated_client.get("/api/reddit/recent")
        assert response.status_code == 200

        returned_points = response.json()["pain_points"]

        # Should only see non-deleted sources
        for point in returned_points:
            if "source_deleted" in point:
                assert point["source_deleted"] is False
            # Deleted points should not appear despite high scores
            assert "Deleted source" not in point["extracted_text"]

    def test_fallback_respects_time_window(self, authenticated_client, db_session):
        """Test that fallback only shows pain points from last 7 days"""
        from app.models.user import User
        from app.models.search_run import SearchRun
        from app.models.pain_point import PainPoint
        import uuid as uuid_lib

        user = db_session.query(User).first()
        if not user:
            user = User(
                id=str(uuid_lib.uuid4()),
                email=f"test_{uuid.uuid4()}@example.com",
                hashed_password="hashed"
            )
            db_session.add(user)
            db_session.commit()

        # Create old search run
        old_search = SearchRun(
            id=str(uuid_lib.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="all",
            created_at=datetime.utcnow() - timedelta(days=10)
        )
        db_session.add(old_search)

        # Create recent search run
        recent_search = SearchRun(
            id=str(uuid_lib.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="24h",
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        db_session.add(recent_search)
        db_session.commit()

        # Add old pain points (>7 days)
        old_point = PainPoint(
            id=str(uuid_lib.uuid4()),
            search_run_id=old_search.id,
            extracted_text="Old pain point",
            relevance_score=0.95,
            sentiment_score=0.0,
            source_reddit_post_ids=["old1"],
            source_deleted=False,
            created_at=datetime.utcnow() - timedelta(days=10)
        )

        # Add recent pain points (<7 days)
        recent_point = PainPoint(
            id=str(uuid_lib.uuid4()),
            search_run_id=recent_search.id,
            extracted_text="Recent pain point",
            relevance_score=0.85,
            sentiment_score=0.0,
            source_reddit_post_ids=["recent1"],
            source_deleted=False,
            created_at=datetime.utcnow() - timedelta(days=2)
        )

        db_session.add_all([old_point, recent_point])
        db_session.commit()

        # Get recent pain points
        response = authenticated_client.get("/api/reddit/recent")
        assert response.status_code == 200

        returned_points = response.json()["pain_points"]

        # Should only see recent pain point
        extracted_texts = [p["extracted_text"] for p in returned_points]
        assert "Recent pain point" in extracted_texts
        assert "Old pain point" not in extracted_texts

    def test_fallback_aggregates_across_all_users(self, client: TestClient, db_session):
        """Test that fallback shows pain points from all users (anonymized)"""
        # Create multiple users with pain points
        users_data = []
        for i in range(3):
            email = f"multi_user_{i}_{uuid.uuid4()}@example.com"
            password = "SecurePassword123"

            # Register user
            reg = client.post("/api/auth/register", json={"email": email, "password": password})
            user_id = reg.json()["user_id"]

            # Login and create search
            login = client.post("/api/auth/login", json={"email": email, "password": password})
            client.cookies.set("access_token", login.cookies.get("access_token"))

            search = client.post(
                "/api/reddit/search",
                json={"topics": [f"user_{i}_topic"], "time_range": "24h"}
            )

            users_data.append({
                "user_id": user_id,
                "email": email,
                "search_id": search.json()["search_run_id"]
            })

        # Login as first user
        login = client.post("/api/auth/login", json={
            "email": users_data[0]["email"],
            "password": "SecurePassword123"
        })
        client.cookies.set("access_token", login.cookies.get("access_token"))

        # Get recent pain points
        response = client.get("/api/reddit/recent")
        assert response.status_code == 200

        pain_points = response.json()["pain_points"]

        # Should potentially see pain points from all users
        # (assuming searches completed and found results)
        # But no user-specific info should be visible
        for point in pain_points:
            assert "user_id" not in point
            assert "search_run_id" not in point  # Internal IDs hidden
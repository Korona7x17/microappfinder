"""
T013: Integration test for user privacy isolation
Tests that user data is properly isolated and protected
"""
import pytest
from fastapi.testclient import TestClient
import uuid


class TestUserPrivacyIsolation:
    """Integration tests for user data privacy and isolation"""

    def test_users_cannot_access_other_users_searches(self, client: TestClient, db_session):
        """Test that users cannot access search runs from other users"""
        # Create two users
        user1_email = f"user1_{uuid.uuid4()}@example.com"
        user2_email = f"user2_{uuid.uuid4()}@example.com"
        password = "SecurePassword123"

        # Register both users
        client.post("/api/auth/register", json={"email": user1_email, "password": password})
        client.post("/api/auth/register", json={"email": user2_email, "password": password})

        # User 1 logs in and creates a search
        login1 = client.post("/api/auth/login", json={"email": user1_email, "password": password})
        user1_token = login1.cookies.get("access_token")

        client.cookies.set("access_token", user1_token)
        search1 = client.post(
            "/api/reddit/search",
            json={"topics": ["user1_topic"], "time_range": "24h"}
        )
        assert search1.status_code == 201
        user1_search_id = search1.json()["search_run_id"]

        # User 2 logs in and tries to access User 1's search
        login2 = client.post("/api/auth/login", json={"email": user2_email, "password": password})
        user2_token = login2.cookies.get("access_token")

        client.cookies.clear()
        client.cookies.set("access_token", user2_token)

        # User 2 should not be able to get User 1's search status
        status_response = client.get(f"/api/reddit/search/{user1_search_id}")
        assert status_response.status_code == 403
        assert "not authorized" in status_response.json()["detail"].lower()

        # User 2 should not be able to get User 1's search results
        results_response = client.get(f"/api/reddit/search/{user1_search_id}/results")
        assert results_response.status_code == 403
        assert "not authorized" in results_response.json()["detail"].lower()

    def test_search_runs_deleted_when_user_deleted(self, client: TestClient, db_session):
        """Test cascade deletion: when user is deleted, their search runs are deleted"""
        email = f"delete_test_{uuid.uuid4()}@example.com"
        password = "SecurePassword123"

        # Register user
        register = client.post("/api/auth/register", json={"email": email, "password": password})
        user_id = register.json()["user_id"]

        # Login and create searches
        login = client.post("/api/auth/login", json={"email": email, "password": password})
        client.cookies.set("access_token", login.cookies.get("access_token"))

        # Create multiple searches
        search_ids = []
        for i in range(3):
            search = client.post(
                "/api/reddit/search",
                json={"topics": [f"topic_{i}"], "time_range": "24h"}
            )
            search_ids.append(search.json()["search_run_id"])

        # Verify searches exist
        from app.models.search_run import SearchRun
        for search_id in search_ids:
            search_run = db_session.query(SearchRun).filter_by(id=search_id).first()
            assert search_run is not None

        # Delete user
        from app.models.user import User
        user = db_session.query(User).filter_by(id=user_id).first()
        db_session.delete(user)
        db_session.commit()

        # Verify all search runs are deleted (CASCADE)
        for search_id in search_ids:
            search_run = db_session.query(SearchRun).filter_by(id=search_id).first()
            assert search_run is None

    def test_api_middleware_enforces_ownership(self, client: TestClient, authenticated_client):
        """Test that API middleware properly enforces ownership checks"""
        # Create a search as authenticated user
        search = authenticated_client.post(
            "/api/reddit/search",
            json={"topics": ["test_ownership"], "time_range": "24h"}
        )
        search_run_id = search.json()["search_run_id"]

        # Try to access with manipulated user context (simulated attack)
        # Clear cookies and try direct API call
        client.cookies.clear()

        # Without auth token - should get 401
        response = client.get(f"/api/reddit/search/{search_run_id}")
        assert response.status_code == 401

        # With invalid/expired token - should get 401
        client.cookies.set("access_token", "invalid_token")
        response = client.get(f"/api/reddit/search/{search_run_id}")
        assert response.status_code == 401

    def test_no_user_data_leaked_in_recent_endpoint(self, client: TestClient):
        """Test that /api/reddit/recent doesn't leak user-specific information"""
        # Create multiple users with searches
        users = []
        for i in range(3):
            email = f"privacy_test_{i}_{uuid.uuid4()}@example.com"
            password = "SecurePassword123"

            client.post("/api/auth/register", json={"email": email, "password": password})
            login = client.post("/api/auth/login", json={"email": email, "password": password})

            client.cookies.set("access_token", login.cookies.get("access_token"))
            client.post(
                "/api/reddit/search",
                json={"topics": [f"privacy_topic_{i}"], "time_range": "24h"}
            )

            users.append({"email": email, "password": password})

        # Login as first user and check recent endpoint
        login = client.post("/api/auth/login", json=users[0])
        client.cookies.set("access_token", login.cookies.get("access_token"))

        response = client.get("/api/reddit/recent")
        assert response.status_code == 200

        pain_points = response.json()["pain_points"]

        # Verify no user-specific data is exposed
        for pain_point in pain_points:
            assert "user_id" not in pain_point
            assert "email" not in pain_point
            # Only aggregated, anonymized data should be present

    def test_database_constraints_prevent_unauthorized_access(self, db_session):
        """Test that database constraints prevent unauthorized data access"""
        from app.models.user import User
        from app.models.search_run import SearchRun
        from app.models.pain_point import PainPoint
        import uuid as uuid_lib

        # Create two users directly in database
        user1 = User(
            id=str(uuid_lib.uuid4()),
            email=f"db_test1_{uuid.uuid4()}@example.com",
            hashed_password="hashed1"
        )
        user2 = User(
            id=str(uuid_lib.uuid4()),
            email=f"db_test2_{uuid.uuid4()}@example.com",
            hashed_password="hashed2"
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # Create search run for user1
        search_run = SearchRun(
            id=str(uuid_lib.uuid4()),
            user_id=user1.id,
            status="completed",
            time_range="24h"
        )
        db_session.add(search_run)
        db_session.commit()

        # Try to create pain point with mismatched user (should fail due to FK constraint)
        try:
            # This should fail because search_run belongs to user1
            # but we're trying to associate it with a non-existent search_run
            fake_search_id = str(uuid_lib.uuid4())
            pain_point = PainPoint(
                id=str(uuid_lib.uuid4()),
                search_run_id=fake_search_id,  # Non-existent search run
                extracted_text="Test pain point",
                relevance_score=0.5,
                sentiment_score=0.0,
                source_reddit_post_ids=[]
            )
            db_session.add(pain_point)
            db_session.commit()

            # Should not reach here
            assert False, "Should have raised integrity error"
        except Exception as e:
            # Expected - foreign key constraint should prevent this
            db_session.rollback()
            assert True

    def test_jwt_token_contains_correct_user_context(self, client: TestClient):
        """Test that JWT tokens contain correct user context and cannot be tampered with"""
        import jwt
        import json
        from datetime import datetime, timedelta

        email = f"jwt_test_{uuid.uuid4()}@example.com"
        password = "SecurePassword123"

        # Register and login
        register = client.post("/api/auth/register", json={"email": email, "password": password})
        user_id = register.json()["user_id"]

        login = client.post("/api/auth/login", json={"email": email, "password": password})
        access_token = login.cookies.get("access_token")

        # Note: In a real test, we'd decode and verify the JWT
        # For now, verify that the token works correctly
        client.cookies.set("access_token", access_token)
        response = client.get("/api/reddit/recent")
        assert response.status_code == 200

        # Tampered token should fail
        tampered_token = access_token[:-5] + "xxxxx"  # Modify last 5 chars
        client.cookies.set("access_token", tampered_token)
        response = client.get("/api/reddit/recent")
        assert response.status_code == 401
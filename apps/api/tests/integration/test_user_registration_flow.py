"""
T011: Integration test for complete user registration flow
Tests end-to-end user registration, login, and authentication flow
"""
import pytest
from fastapi.testclient import TestClient
import uuid
import time


class TestUserRegistrationFlow:
    """Integration tests for complete user registration and authentication flow"""

    def test_complete_registration_to_authenticated_request_flow(self, client: TestClient, db_session):
        """Test complete flow: register -> login -> authenticated request -> refresh"""
        email = f"integration_test_{uuid.uuid4()}@example.com"
        password = "SecurePassword123"

        # Step 1: Register new user
        register_response = client.post(
            "/api/auth/register",
            json={"email": email, "password": password}
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["user_id"]

        # Verify user exists in database
        from app.models.user import User
        user = db_session.query(User).filter_by(id=user_id).first()
        assert user is not None
        assert user.email == email
        assert user.hashed_password != password  # Password is hashed

        # Step 2: Login with new credentials
        login_response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password}
        )
        assert login_response.status_code == 200
        assert login_response.json()["user_id"] == user_id

        # Extract tokens from cookies
        access_token = login_response.cookies.get("access_token")
        refresh_token = login_response.cookies.get("refresh_token")
        assert access_token is not None
        assert refresh_token is not None

        # Step 3: Make authenticated request
        client.cookies.set("access_token", access_token)
        auth_response = client.get("/api/reddit/recent")
        assert auth_response.status_code == 200

        # Step 4: Refresh token
        client.cookies.clear()
        client.cookies.set("refresh_token", refresh_token)
        refresh_response = client.post("/api/auth/refresh")
        assert refresh_response.status_code == 200

        # Step 5: Use new access token
        new_access_token = refresh_response.cookies.get("access_token")
        assert new_access_token is not None
        assert new_access_token != access_token  # New token issued

        client.cookies.set("access_token", new_access_token)
        final_response = client.get("/api/reddit/recent")
        assert final_response.status_code == 200

    def test_registration_with_duplicate_email_handling(self, client: TestClient):
        """Test registration flow handles duplicate emails gracefully"""
        email = f"duplicate_test_{uuid.uuid4()}@example.com"
        password = "SecurePassword123"

        # First registration succeeds
        response1 = client.post(
            "/api/auth/register",
            json={"email": email, "password": password}
        )
        assert response1.status_code == 201
        user_id_1 = response1.json()["user_id"]

        # Second registration with same email fails
        response2 = client.post(
            "/api/auth/register",
            json={"email": email, "password": "DifferentPassword456"}
        )
        assert response2.status_code == 409

        # Original user can still login
        login_response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password}
        )
        assert login_response.status_code == 200
        assert login_response.json()["user_id"] == user_id_1

    def test_registration_validation_prevents_weak_accounts(self, client: TestClient, db_session):
        """Test that registration validation prevents creation of weak accounts"""
        test_cases = [
            {"email": "invalid-email", "password": "ValidPass123"},  # Invalid email
            {"email": "test@example.com", "password": "weak"},  # Weak password
            {"email": "", "password": "ValidPass123"},  # Empty email
            {"email": "test@example.com", "password": ""},  # Empty password
        ]

        for test_case in test_cases:
            response = client.post("/api/auth/register", json=test_case)
            assert response.status_code == 422

            # Verify no user was created
            from app.models.user import User
            user = db_session.query(User).filter_by(email=test_case["email"]).first()
            assert user is None

    def test_token_expiration_and_refresh_cycle(self, client: TestClient):
        """Test token expiration and refresh cycle"""
        email = f"token_test_{uuid.uuid4()}@example.com"
        password = "SecurePassword123"

        # Register and login
        client.post("/api/auth/register", json={"email": email, "password": password})
        login_response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password}
        )

        access_token = login_response.cookies.get("access_token")
        refresh_token = login_response.cookies.get("refresh_token")

        # Access token should work initially
        client.cookies.set("access_token", access_token)
        response = client.get("/api/reddit/recent")
        assert response.status_code == 200

        # Simulate expired access token (would need to wait 15 min in reality)
        # For testing, we'll use an invalid token to simulate expiration
        client.cookies.set("access_token", "expired_token_simulation")
        response = client.get("/api/reddit/recent")
        assert response.status_code == 401

        # Refresh should still work with valid refresh token
        client.cookies.clear()
        client.cookies.set("refresh_token", refresh_token)
        refresh_response = client.post("/api/auth/refresh")
        assert refresh_response.status_code == 200

        # New access token should work
        new_access_token = refresh_response.cookies.get("access_token")
        client.cookies.set("access_token", new_access_token)
        response = client.get("/api/reddit/recent")
        assert response.status_code == 200

    def test_logout_invalidates_tokens(self, client: TestClient, authenticated_client):
        """Test that logout properly invalidates tokens"""
        # Authenticated client can make requests
        response = authenticated_client.get("/api/reddit/recent")
        assert response.status_code == 200

        # Logout
        logout_response = authenticated_client.post("/api/auth/logout")
        assert logout_response.status_code == 200

        # Tokens should be cleared
        assert logout_response.cookies.get("access_token") == ""
        assert logout_response.cookies.get("refresh_token") == ""

        # Subsequent requests should fail
        response = authenticated_client.get("/api/reddit/recent")
        assert response.status_code == 401

    def test_concurrent_registrations_handled_correctly(self, client: TestClient):
        """Test that concurrent registrations are handled without race conditions"""
        import threading
        import queue

        email = f"concurrent_test_{uuid.uuid4()}@example.com"
        password = "SecurePassword123"
        results = queue.Queue()

        def register():
            response = client.post(
                "/api/auth/register",
                json={"email": email, "password": password}
            )
            results.put(response.status_code)

        # Start multiple concurrent registration attempts
        threads = []
        for _ in range(5):
            t = threading.Thread(target=register)
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Collect results
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())

        # Exactly one should succeed (201), others should get conflict (409)
        assert status_codes.count(201) == 1
        assert status_codes.count(409) == 4
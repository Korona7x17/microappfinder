"""
T005: Contract test for POST /api/auth/login
Tests user login endpoint contract compliance
"""
import pytest
from fastapi.testclient import TestClient
import uuid


class TestAuthLoginContract:
    """Contract tests for POST /api/auth/login endpoint"""

    def test_successful_login_returns_200(self, client: TestClient, registered_user):
        """Test successful login returns 200 with user_id and tokens"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "user_id" in data
        assert data["user_id"] == registered_user["user_id"]

        # Verify cookies are set
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert cookies["access_token"]["httponly"] is True
        assert cookies["refresh_token"]["httponly"] is True
        assert cookies["access_token"]["max-age"] == "900"  # 15 minutes
        assert cookies["refresh_token"]["max-age"] == "604800"  # 7 days

    def test_invalid_email_returns_401(self, client: TestClient):
        """Test login with non-existent email returns 401 Unauthorized"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123"
            }
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_invalid_password_returns_401(self, client: TestClient, registered_user):
        """Test login with wrong password returns 401 Unauthorized"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": registered_user["email"],
                "password": "WrongPassword123"
            }
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_missing_required_fields_returns_422(self, client: TestClient):
        """Test login with missing required fields returns 422"""
        # Missing email
        response = client.post(
            "/api/auth/login",
            json={"password": "SomePassword123"}
        )
        assert response.status_code == 422

        # Missing password
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 422

        # Empty body
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422

    def test_invalid_email_format_returns_422(self, client: TestClient):
        """Test login with invalid email format returns 422"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "not-an-email",
                "password": "SomePassword123"
            }
        )

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("email" in str(error).lower() for error in errors)

    def test_rate_limiting_after_failed_attempts(self, client: TestClient):
        """Test that login is rate-limited after multiple failed attempts"""
        email = f"ratelimit_{uuid.uuid4()}@example.com"

        # Make 5 failed login attempts
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={"email": email, "password": "WrongPassword"}
            )
            assert response.status_code == 401

        # 6th attempt should be rate-limited
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "WrongPassword"}
        )

        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()
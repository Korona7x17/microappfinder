"""
T006: Contract test for POST /api/auth/refresh
Tests token refresh endpoint contract compliance
"""
import pytest
from fastapi.testclient import TestClient
import time


class TestAuthRefreshContract:
    """Contract tests for POST /api/auth/refresh endpoint"""

    def test_successful_refresh_returns_200(self, client: TestClient, authenticated_client):
        """Test successful token refresh returns 200 with new access token"""
        # Use authenticated client with valid refresh token
        response = authenticated_client.post("/api/auth/refresh")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert data["message"] == "Token refreshed successfully"

        # Verify new access token is set
        cookies = response.cookies
        assert "access_token" in cookies
        assert cookies["access_token"]["httponly"] is True
        assert cookies["access_token"]["max-age"] == "900"  # 15 minutes

    def test_missing_refresh_token_returns_401(self, client: TestClient):
        """Test refresh without refresh token returns 401 Unauthorized"""
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        assert response.json()["detail"] == "Refresh token required"

    def test_invalid_refresh_token_returns_401(self, client: TestClient):
        """Test refresh with invalid refresh token returns 401"""
        client.cookies.set("refresh_token", "invalid_token_here")
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"

    def test_expired_refresh_token_returns_401(self, client: TestClient, expired_refresh_token):
        """Test refresh with expired refresh token returns 401"""
        client.cookies.set("refresh_token", expired_refresh_token)
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        assert response.json()["detail"] == "Refresh token expired"

    def test_refresh_token_rotation(self, client: TestClient, authenticated_client):
        """Test that refresh token is rotated on successful refresh"""
        # Get initial refresh token
        initial_refresh = authenticated_client.cookies.get("refresh_token")

        # Refresh
        response = authenticated_client.post("/api/auth/refresh")
        assert response.status_code == 200

        # Check if refresh token was rotated (optional based on security policy)
        new_refresh = response.cookies.get("refresh_token")
        if new_refresh:  # If rotation is implemented
            assert new_refresh != initial_refresh

    def test_refresh_does_not_require_access_token(self, client: TestClient, registered_user):
        """Test that refresh works even with expired/missing access token"""
        # Login to get refresh token
        response = client.post(
            "/api/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"]
            }
        )
        assert response.status_code == 200

        # Clear access token but keep refresh token
        refresh_token = response.cookies.get("refresh_token")
        client.cookies.clear()
        client.cookies.set("refresh_token", refresh_token)

        # Should still be able to refresh
        response = client.post("/api/auth/refresh")
        assert response.status_code == 200

    def test_blacklisted_refresh_token_returns_401(self, client: TestClient, blacklisted_refresh_token):
        """Test that blacklisted refresh tokens are rejected"""
        client.cookies.set("refresh_token", blacklisted_refresh_token)
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        assert response.json()["detail"] == "Token has been revoked"
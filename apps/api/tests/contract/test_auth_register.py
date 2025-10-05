"""
T004: Contract test for POST /api/auth/register
Tests user registration endpoint contract compliance
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid


class TestAuthRegisterContract:
    """Contract tests for POST /api/auth/register endpoint"""

    def test_successful_registration_returns_201(self, client: TestClient):
        """Test successful registration returns 201 with user_id and tokens"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": f"test_{uuid.uuid4()}@example.com",
                "password": "SecurePass123"
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure per OpenAPI spec
        assert "user_id" in data
        assert isinstance(data["user_id"], str)
        assert len(data["user_id"]) == 36  # UUID format

        # Verify cookies are set
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert cookies["access_token"]["httponly"] is True
        assert cookies["refresh_token"]["httponly"] is True
        assert cookies["access_token"]["samesite"] == "Strict"
        assert cookies["refresh_token"]["samesite"] == "Strict"

    def test_duplicate_email_returns_409(self, client: TestClient):
        """Test registration with existing email returns 409 Conflict"""
        email = f"duplicate_{uuid.uuid4()}@example.com"

        # First registration
        response = client.post(
            "/api/auth/register",
            json={"email": email, "password": "SecurePass123"}
        )
        assert response.status_code == 201

        # Duplicate registration
        response = client.post(
            "/api/auth/register",
            json={"email": email, "password": "DifferentPass456"}
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_invalid_email_format_returns_422(self, client: TestClient):
        """Test registration with invalid email format returns 422"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123"
            }
        )

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("email" in str(error).lower() for error in errors)

    def test_weak_password_returns_422(self, client: TestClient):
        """Test registration with weak password returns 422"""
        test_cases = [
            "short",  # Too short (< 8 chars)
            "alllowercase",  # No uppercase
            "ALLUPPERCASE",  # No lowercase
            "NoNumbers",  # No digits
        ]

        for weak_password in test_cases:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"test_{uuid.uuid4()}@example.com",
                    "password": weak_password
                }
            )

            assert response.status_code == 422, f"Password '{weak_password}' should be rejected"
            errors = response.json()["detail"]
            assert any("password" in str(error).lower() for error in errors)

    def test_missing_required_fields_returns_422(self, client: TestClient):
        """Test registration with missing required fields returns 422"""
        # Missing email
        response = client.post(
            "/api/auth/register",
            json={"password": "SecurePass123"}
        )
        assert response.status_code == 422

        # Missing password
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 422

        # Empty body
        response = client.post("/api/auth/register", json={})
        assert response.status_code == 422

    def test_password_is_hashed_in_database(self, client: TestClient, db_session):
        """Test that password is stored as bcrypt hash, not plaintext"""
        email = f"hash_test_{uuid.uuid4()}@example.com"
        password = "SecurePass123"

        response = client.post(
            "/api/auth/register",
            json={"email": email, "password": password}
        )

        assert response.status_code == 201
        user_id = response.json()["user_id"]

        # Query database directly
        from app.models.user import User
        user = db_session.query(User).filter_by(id=user_id).first()

        assert user is not None
        assert user.hashed_password != password  # Not plaintext
        assert user.hashed_password.startswith("$2b$")  # bcrypt hash
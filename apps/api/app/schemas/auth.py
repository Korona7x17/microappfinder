"""
T021: Auth schemas
Pydantic models for authentication endpoints per contracts/openapi.yaml
"""
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional
import re


class RegisterRequest(BaseModel):
    """Request body for POST /api/auth/register"""
    email: EmailStr = Field(..., description="User email address (RFC 5322 format)")
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 chars, requires uppercase + lowercase + digit)"
    )

    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password contains uppercase, lowercase, and digit"""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class LoginRequest(BaseModel):
    """Request body for POST /api/auth/login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class AuthResponse(BaseModel):
    """Response for successful authentication (register/login)"""
    user_id: str = Field(..., description="UUID of authenticated user")
    message: str = Field(default="Authentication successful")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Authentication successful"
            }
        }


class UserProfile(BaseModel):
    """Response for GET /api/auth/me"""
    user_id: str = Field(..., description="UUID of current user")
    email: str = Field(..., description="User email address")
    created_at: datetime = Field(..., description="Account creation timestamp")
    total_searches: int = Field(default=0, description="Total number of searches performed")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "created_at": "2025-10-04T12:00:00Z",
                "total_searches": 5
            }
        }


class RefreshResponse(BaseModel):
    """Response for POST /api/auth/refresh"""
    message: str = Field(default="Token refreshed successfully")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Token refreshed successfully"
            }
        }


class LogoutResponse(BaseModel):
    """Response for POST /api/auth/logout"""
    message: str = Field(default="Logged out successfully")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Logged out successfully"
            }
        }

"""
T024: Auth service
Authentication service with bcrypt password hashing and JWT token generation
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os


class AuthService:
    """
    Authentication service

    Features:
    - bcrypt password hashing (cost factor 12)
    - JWT access tokens (15 min expiry)
    - JWT refresh tokens (7 day expiry)
    - httponly cookie support
    """

    # bcrypt context with cost factor 12
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

    # JWT configuration
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-256-bit-secret-key-change-this-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash password using bcrypt with cost factor 12

        Args:
            password: Plain text password

        Returns:
            str: bcrypt hashed password (starts with $2b$12$)
        """
        return cls.pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against bcrypt hash

        Args:
            plain_password: Plain text password to verify
            hashed_password: bcrypt hash from database

        Returns:
            bool: True if password matches, False otherwise
        """
        return cls.pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def create_access_token(cls, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token

        Args:
            data: Payload dictionary (should include 'sub' with user_id)
            expires_delta: Custom expiration (default: 15 minutes)

        Returns:
            str: JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt

    @classmethod
    def create_refresh_token(cls, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT refresh token

        Args:
            data: Payload dictionary (should include 'sub' with user_id)
            expires_delta: Custom expiration (default: 7 days)

        Returns:
            str: JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt

    @classmethod
    def decode_token(cls, token: str) -> dict:
        """
        Decode and verify JWT token

        Args:
            token: JWT token string

        Returns:
            dict: Decoded payload

        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except JWTError as e:
            raise JWTError(f"Invalid token: {str(e)}")

    @classmethod
    def verify_token(cls, token: str, token_type: str = "access") -> Optional[str]:
        """
        Verify token and extract user_id

        Args:
            token: JWT token string
            token_type: Expected token type ('access' or 'refresh')

        Returns:
            str: user_id if valid, None otherwise
        """
        try:
            payload = cls.decode_token(token)

            # Verify token type
            if payload.get("type") != token_type:
                return None

            # Extract user_id from 'sub' claim
            user_id: str = payload.get("sub")
            if user_id is None:
                return None

            return user_id

        except JWTError:
            return None

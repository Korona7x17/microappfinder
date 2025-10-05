"""
T029 & T030: JWT auth dependency and ownership middleware
FastAPI dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError

from app.models.user import User
from app.models.search_run import SearchRun
from app.services.auth_service import AuthService
from app.database import get_db


# HTTP Bearer scheme for token authentication
security = HTTPBearer(auto_error=False)


async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    T029: JWT auth dependency

    Extract and verify current user from JWT token (cookie or Authorization header)

    Args:
        access_token: JWT token from httponly cookie
        authorization: JWT token from Authorization header
        db: Database session

    Returns:
        User: Authenticated user object

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try to get token from cookie first, then Authorization header
    token = None
    if access_token:
        token = access_token
    elif authorization:
        token = authorization.credentials

    if token is None:
        raise credentials_exception

    try:
        # Verify and decode token
        user_id = AuthService.verify_token(token, token_type="access")

        if user_id is None:
            raise credentials_exception

        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception


async def verify_run_ownership(
    search_run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SearchRun:
    """
    T030: Ownership middleware

    Verify that current user owns the search run (403 if mismatch)

    Args:
        search_run_id: UUID of search run
        current_user: Authenticated user from get_current_user dependency
        db: Database session

    Returns:
        SearchRun: Search run object if user is owner

    Raises:
        HTTPException: 404 if search run not found
        HTTPException: 403 if user doesn't own the search run
    """
    # Fetch search run
    search_run = db.query(SearchRun).filter(SearchRun.id == search_run_id).first()

    if search_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search run not found"
        )

    # Verify ownership
    if str(search_run.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this search run"
        )

    return search_run


async def get_optional_user(
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional auth dependency (doesn't raise 401 if not authenticated)

    Returns:
        User: Authenticated user or None
    """
    if access_token is None and authorization is None:
        return None

    try:
        # Try to get token
        token = access_token if access_token else (authorization.credentials if authorization else None)

        if token is None:
            return None

        # Verify and decode token
        user_id = AuthService.verify_token(token, token_type="access")

        if user_id is None:
            return None

        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()
        return user

    except Exception:
        return None


async def get_refresh_token_user(
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Verify refresh token and return user

    Args:
        refresh_token: JWT refresh token from cookie
        db: Database session

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: 401 if token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token required"
    )

    if refresh_token is None:
        raise credentials_exception

    try:
        # Verify refresh token
        user_id = AuthService.verify_token(refresh_token, token_type="refresh")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Fetch user
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

"""
T027: Auth endpoints
Authentication and user management endpoints per contracts/openapi.yaml
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserProfile,
    RefreshResponse,
    LogoutResponse
)
from app.services.auth_service import AuthService
from app.core.auth import get_current_user, get_refresh_token_user


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    POST /api/auth/register

    Register new user account

    Returns:
        - 201: User created successfully with JWT tokens in httponly cookies
        - 409: Email already exists
        - 422: Validation error (invalid email or weak password)
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )

    # Hash password
    hashed_password = AuthService.hash_password(request.password)

    # Create user
    new_user = User(
        email=request.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate tokens
    access_token = AuthService.create_access_token(data={"sub": str(new_user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(new_user.id)})

    # Set httponly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="strict",
        max_age=900,  # 15 minutes
        secure=False  # Set to True in production with HTTPS
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="strict",
        max_age=604800,  # 7 days
        secure=False
    )

    return AuthResponse(
        user_id=str(new_user.id),
        message="Registration successful"
    )


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    POST /api/auth/login

    Authenticate user and issue JWT tokens

    Returns:
        - 200: Login successful with JWT tokens in httponly cookies
        - 401: Invalid credentials
        - 422: Validation error
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not AuthService.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate tokens
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

    # Set httponly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="strict",
        max_age=900,  # 15 minutes
        secure=False
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="strict",
        max_age=604800,  # 7 days
        secure=False
    )

    return AuthResponse(
        user_id=str(user.id),
        message="Login successful"
    )


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh(
    response: Response,
    current_user: User = Depends(get_refresh_token_user)
):
    """
    POST /api/auth/refresh

    Refresh access token using refresh token

    Returns:
        - 200: New access token issued
        - 401: Invalid or expired refresh token
    """
    # Generate new access token
    access_token = AuthService.create_access_token(data={"sub": str(current_user.id)})

    # Set new access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="strict",
        max_age=900,  # 15 minutes
        secure=False
    )

    return RefreshResponse(message="Token refreshed successfully")


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout(response: Response):
    """
    POST /api/auth/logout

    Logout user by clearing cookies

    Returns:
        - 200: Logged out successfully
    """
    # Clear cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return LogoutResponse(message="Logged out successfully")


@router.get("/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GET /api/auth/me

    Get current user profile

    Returns:
        - 200: User profile
        - 401: Not authenticated
    """
    # Count total searches
    from app.models.search_run import SearchRun
    total_searches = db.query(func.count(SearchRun.id)).filter(
        SearchRun.user_id == current_user.id
    ).scalar()

    return UserProfile(
        user_id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at,
        total_searches=total_searches or 0
    )

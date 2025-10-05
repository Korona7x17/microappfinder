"""
Pytest configuration and fixtures for API tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, timedelta


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a database session for tests"""
    Session = sessionmaker(bind=db_engine)
    session = Session()

    # Create tables
    from app.models import Base
    Base.metadata.create_all(db_engine)

    yield session

    session.close()
    Base.metadata.drop_all(db_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create FastAPI test client"""
    from app.main import app
    from app.database import get_db

    # Override database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    """Create a registered user for tests"""
    email = f"test_{uuid.uuid4()}@example.com"
    password = "SecurePassword123"

    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password}
    )

    return {
        "user_id": response.json()["user_id"],
        "email": email,
        "password": password
    }


@pytest.fixture
def authenticated_client(client, registered_user):
    """Create an authenticated test client"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"]
        }
    )

    client.cookies.set("access_token", response.cookies.get("access_token"))
    client.cookies.set("refresh_token", response.cookies.get("refresh_token"))

    return client


@pytest.fixture
def active_search_run(authenticated_client):
    """Create an active search run"""
    response = authenticated_client.post(
        "/api/reddit/search",
        json={
            "topics": ["test topic"],
            "time_range": "24h"
        }
    )

    return {
        "search_run_id": response.json()["search_run_id"],
        "status": response.json()["status"]
    }


@pytest.fixture
def completed_search_with_results(authenticated_client, db_session):
    """Create a completed search with pain points"""
    from app.models.search_run import SearchRun
    from app.models.pain_point import PainPoint
    from app.models.user import User
    import uuid as uuid_lib

    # Get current user
    user = db_session.query(User).first()

    # Create completed search run
    search_run = SearchRun(
        id=str(uuid_lib.uuid4()),
        user_id=user.id,
        status="completed",
        time_range="7days",
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        pain_points_count=3
    )
    db_session.add(search_run)

    # Add pain points
    for i in range(3):
        pain_point = PainPoint(
            id=str(uuid_lib.uuid4()),
            search_run_id=search_run.id,
            extracted_text=f"Pain point {i}: Users struggle with task management",
            relevance_score=0.9 - (i * 0.1),
            sentiment_score=-0.3,
            source_reddit_post_ids=[f"post_{i}"],
            source_deleted=False,
            created_at=datetime.utcnow()
        )
        db_session.add(pain_point)

    db_session.commit()

    return {"search_run_id": search_run.id}


@pytest.fixture
def expired_refresh_token():
    """Create an expired refresh token for testing"""
    # This would normally create a JWT with expired timestamp
    return "expired_token_simulation"


@pytest.fixture
def blacklisted_refresh_token():
    """Create a blacklisted refresh token for testing"""
    return "blacklisted_token_simulation"


@pytest.fixture
def other_users_search_run(client, db_session):
    """Create a search run belonging to another user"""
    from app.models.user import User
    from app.models.search_run import SearchRun
    import uuid as uuid_lib

    # Create another user
    other_user = User(
        id=str(uuid_lib.uuid4()),
        email=f"other_{uuid.uuid4()}@example.com",
        hashed_password="hashed"
    )
    db_session.add(other_user)

    # Create their search run
    search_run = SearchRun(
        id=str(uuid_lib.uuid4()),
        user_id=other_user.id,
        status="completed",
        time_range="24h"
    )
    db_session.add(search_run)
    db_session.commit()

    return {"search_run_id": search_run.id}


@pytest.fixture
def pending_search_run(authenticated_client, db_session):
    """Create a pending search run"""
    from app.models.search_run import SearchRun
    from app.models.user import User
    import uuid as uuid_lib

    user = db_session.query(User).first()

    search_run = SearchRun(
        id=str(uuid_lib.uuid4()),
        user_id=user.id,
        status="pending",
        time_range="24h"
    )
    db_session.add(search_run)
    db_session.commit()

    return {"search_run_id": search_run.id}


@pytest.fixture
def in_progress_search_run(authenticated_client, db_session):
    """Create an in-progress search run"""
    from app.models.search_run import SearchRun
    from app.models.user import User
    import uuid as uuid_lib

    user = db_session.query(User).first()

    search_run = SearchRun(
        id=str(uuid_lib.uuid4()),
        user_id=user.id,
        status="in_progress",
        time_range="7days",
        started_at=datetime.utcnow()
    )
    db_session.add(search_run)
    db_session.commit()

    return {"search_run_id": search_run.id}


@pytest.fixture
def failed_search_run(authenticated_client, db_session):
    """Create a failed search run"""
    from app.models.search_run import SearchRun
    from app.models.user import User
    import uuid as uuid_lib

    user = db_session.query(User).first()

    search_run = SearchRun(
        id=str(uuid_lib.uuid4()),
        user_id=user.id,
        status="failed",
        time_range="24h",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        error_message="Reddit API rate limit exceeded"
    )
    db_session.add(search_run)
    db_session.commit()

    return {"search_run_id": search_run.id}


@pytest.fixture
def empty_database(db_session):
    """Ensure database is empty"""
    # Clear all tables
    from app.models import Base
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()

    return db_session


@pytest.fixture
def mock_reddit_api(monkeypatch):
    """Mock Reddit API responses"""
    def mock_search(*args, **kwargs):
        return [
            {
                "id": "t3_abc123",
                "title": "Need help with productivity",
                "selftext": "I struggle with time management",
                "score": 42,
                "num_comments": 15,
                "created_utc": datetime.utcnow().timestamp(),
                "subreddit": "productivity",
                "author": "test_user",
                "url": "https://reddit.com/r/productivity/abc123"
            }
        ]

    # Mock PRAW or Reddit service
    monkeypatch.setattr("app.services.reddit_service.search_reddit", mock_search)

    return mock_search
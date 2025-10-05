"""
T007: Unit tests for SearchRun source tracking
Tests sources_queried and hn_items_fetched columns
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import uuid


class TestSearchRunSourceTracking:
    """Unit tests for SearchRun source tracking updates"""

    def test_search_run_with_reddit_only_source(self, db_session):
        """Test creating search run with Reddit-only source"""
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create search run with Reddit only
        search_run = SearchRun(
            user_id=user.id,
            status="pending",
            time_range="7days",
            sources_queried=["reddit"]
        )
        db_session.add(search_run)
        db_session.commit()

        # Verify
        assert search_run.sources_queried == ["reddit"]
        assert search_run.hn_items_fetched is None

    def test_search_run_with_hackernews_source(self, db_session):
        """Test creating search run with HackerNews source"""
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create search run with HackerNews
        search_run = SearchRun(
            user_id=user.id,
            status="completed",
            time_range="24h",
            sources_queried=["hackernews"],
            hn_items_fetched=15
        )
        db_session.add(search_run)
        db_session.commit()

        # Verify
        assert search_run.sources_queried == ["hackernews"]
        assert search_run.hn_items_fetched == 15

    def test_search_run_with_multiple_sources(self, db_session):
        """Test creating search run querying both Reddit and HackerNews"""
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create search run with multiple sources
        search_run = SearchRun(
            user_id=user.id,
            status="completed",
            time_range="30days",
            sources_queried=["reddit", "hackernews"],
            hn_items_fetched=42
        )
        db_session.add(search_run)
        db_session.commit()

        # Verify
        assert "reddit" in search_run.sources_queried
        assert "hackernews" in search_run.sources_queried
        assert len(search_run.sources_queried) == 2
        assert search_run.hn_items_fetched == 42

    def test_sources_queried_defaults_to_reddit(self, db_session):
        """Test that sources_queried defaults to ['reddit'] for backward compatibility"""
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create search run without specifying sources_queried
        search_run = SearchRun(
            user_id=user.id,
            status="pending",
            time_range="7days"
            # sources_queried not specified
        )
        db_session.add(search_run)
        db_session.commit()

        # Should default to ["reddit"]
        assert search_run.sources_queried == ["reddit"]

    def test_hn_items_fetched_nullable(self, db_session):
        """Test that hn_items_fetched can be null (Reddit-only searches)"""
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create Reddit-only search run
        search_run = SearchRun(
            user_id=user.id,
            status="completed",
            time_range="24h",
            sources_queried=["reddit"],
            hn_items_fetched=None
        )
        db_session.add(search_run)
        db_session.commit()

        # Verify null is allowed
        assert search_run.hn_items_fetched is None

    def test_hn_items_fetched_check_constraint_positive(self, db_session):
        """Test that hn_items_fetched must be >= 0 when not null"""
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Try to create with negative hn_items_fetched
        search_run = SearchRun(
            user_id=user.id,
            status="completed",
            time_range="7days",
            sources_queried=["hackernews"],
            hn_items_fetched=-5
        )
        db_session.add(search_run)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_hn_items_fetched_zero_allowed(self, db_session):
        """Test that hn_items_fetched can be 0 (no HN results found)"""
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create search run with 0 HN items
        search_run = SearchRun(
            user_id=user.id,
            status="completed",
            time_range="24h",
            sources_queried=["reddit", "hackernews"],
            hn_items_fetched=0
        )
        db_session.add(search_run)
        db_session.commit()

        # Verify 0 is allowed
        assert search_run.hn_items_fetched == 0

    def test_query_search_runs_by_source(self, db_session):
        """Test filtering search runs by sources_queried"""
        from app.models.search_run import SearchRun
        from app.models.user import User
        from sqlalchemy import func

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create Reddit-only search runs
        for i in range(3):
            search_run = SearchRun(
                user_id=user.id,
                status="completed",
                time_range="7days",
                sources_queried=["reddit"]
            )
            db_session.add(search_run)

        # Create multi-source search runs
        for i in range(2):
            search_run = SearchRun(
                user_id=user.id,
                status="completed",
                time_range="7days",
                sources_queried=["reddit", "hackernews"],
                hn_items_fetched=10 + i
            )
            db_session.add(search_run)

        db_session.commit()

        # Query runs that include HackerNews
        # Using JSONB contains operator
        hn_runs = db_session.query(SearchRun).filter(
            SearchRun.sources_queried.contains(["hackernews"])
        ).all()

        assert len(hn_runs) == 2
        assert all("hackernews" in run.sources_queried for run in hn_runs)

    def test_sources_queried_preserves_order(self, db_session):
        """Test that sources_queried maintains insertion order"""
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create with specific order
        search_run = SearchRun(
            user_id=user.id,
            status="completed",
            time_range="7days",
            sources_queried=["hackernews", "reddit"]
        )
        db_session.add(search_run)
        db_session.commit()

        # Re-fetch to verify order persistence
        db_session.expunge_all()
        retrieved = db_session.query(SearchRun).filter_by(id=search_run.id).first()

        assert retrieved.sources_queried == ["hackernews", "reddit"]
        assert retrieved.sources_queried[0] == "hackernews"
        assert retrieved.sources_queried[1] == "reddit"

    def test_update_hn_items_fetched_after_processing(self, db_session):
        """Test updating hn_items_fetched after HN search completes"""
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create pending search run
        search_run = SearchRun(
            user_id=user.id,
            status="in_progress",
            time_range="7days",
            sources_queried=["reddit", "hackernews"],
            hn_items_fetched=None
        )
        db_session.add(search_run)
        db_session.commit()

        # Update after HN fetch completes
        search_run.hn_items_fetched = 25
        search_run.status = "completed"
        db_session.commit()

        # Verify update
        assert search_run.hn_items_fetched == 25
        assert search_run.status == "completed"

    def test_sources_queried_supports_future_platforms(self, db_session):
        """Test that sources_queried can include future platforms"""
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create with future platform names
        search_run = SearchRun(
            user_id=user.id,
            status="completed",
            time_range="7days",
            sources_queried=["reddit", "hackernews", "producthunt", "indiehackers"]
        )
        db_session.add(search_run)
        db_session.commit()

        # Verify extensibility
        assert len(search_run.sources_queried) == 4
        assert "producthunt" in search_run.sources_queried
        assert "indiehackers" in search_run.sources_queried

    def test_hn_statistics_aggregation(self, db_session):
        """Test aggregating HN fetch statistics across search runs"""
        from app.models.search_run import SearchRun
        from app.models.user import User
        from sqlalchemy import func

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # Create search runs with varying HN fetch counts
        hn_counts = [10, 25, 0, 15, None]
        for count in hn_counts:
            search_run = SearchRun(
                user_id=user.id,
                status="completed",
                time_range="7days",
                sources_queried=["reddit", "hackernews"] if count is not None else ["reddit"],
                hn_items_fetched=count
            )
            db_session.add(search_run)
        db_session.commit()

        # Calculate total HN items fetched (excluding nulls)
        total_hn = db_session.query(func.sum(SearchRun.hn_items_fetched)).scalar()
        avg_hn = db_session.query(func.avg(SearchRun.hn_items_fetched)).scalar()

        assert total_hn == 50  # 10 + 25 + 0 + 15 = 50
        assert avg_hn == 12.5  # 50 / 4 = 12.5 (null excluded from avg)

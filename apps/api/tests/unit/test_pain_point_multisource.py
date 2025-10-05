"""
T006: Unit tests for PainPoint multi-source support
Tests source_platform and source_post_ids columns
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import uuid


class TestPainPointMultiSource:
    """Unit tests for PainPoint multi-source updates"""

    def test_pain_point_with_reddit_source(self, db_session):
        """Test creating pain point with Reddit as source platform"""
        from app.models.pain_point import PainPoint
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user and search run
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)

        search_run = SearchRun(
            id=str(uuid.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="7days"
        )
        db_session.add(search_run)
        db_session.commit()

        # Create pain point with Reddit source
        pain_point = PainPoint(
            search_run_id=search_run.id,
            extracted_text="Users struggle with task prioritization",
            relevance_score=0.85,
            sentiment_score=-0.4,
            source_platform="reddit",
            source_post_ids=["t3_abc123", "t3_def456"]
        )
        db_session.add(pain_point)
        db_session.commit()

        # Verify
        assert pain_point.source_platform == "reddit"
        assert pain_point.source_post_ids == ["t3_abc123", "t3_def456"]

    def test_pain_point_with_hackernews_source(self, db_session):
        """Test creating pain point with HackerNews as source platform"""
        from app.models.pain_point import PainPoint
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user and search run
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)

        search_run = SearchRun(
            id=str(uuid.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="7days"
        )
        db_session.add(search_run)
        db_session.commit()

        # Create pain point with HackerNews source
        pain_point = PainPoint(
            search_run_id=search_run.id,
            extracted_text="Need better API documentation tools",
            relevance_score=0.92,
            sentiment_score=-0.3,
            source_platform="hackernews",
            source_post_ids=["12345678", "87654321"]
        )
        db_session.add(pain_point)
        db_session.commit()

        # Verify
        assert pain_point.source_platform == "hackernews"
        assert pain_point.source_post_ids == ["12345678", "87654321"]

    def test_source_platform_defaults_to_reddit(self, db_session):
        """Test that source_platform defaults to 'reddit' for backward compatibility"""
        from app.models.pain_point import PainPoint
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user and search run
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)

        search_run = SearchRun(
            id=str(uuid.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="7days"
        )
        db_session.add(search_run)
        db_session.commit()

        # Create pain point without specifying source_platform
        pain_point = PainPoint(
            search_run_id=search_run.id,
            extracted_text="Default source platform test",
            relevance_score=0.75,
            sentiment_score=-0.2,
            source_post_ids=["t3_xyz789"]
        )
        db_session.add(pain_point)
        db_session.commit()

        # Should default to 'reddit'
        assert pain_point.source_platform == "reddit"

    def test_source_post_ids_supports_mixed_sources(self, db_session):
        """Test that source_post_ids can store IDs from multiple sources"""
        from app.models.pain_point import PainPoint
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user and search run
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)

        search_run = SearchRun(
            id=str(uuid.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="7days"
        )
        db_session.add(search_run)
        db_session.commit()

        # Create pain point with mixed source IDs (deduplicated across sources)
        pain_point = PainPoint(
            search_run_id=search_run.id,
            extracted_text="Cross-platform pain point aggregation",
            relevance_score=0.88,
            sentiment_score=-0.5,
            source_platform="reddit",  # Primary source
            source_post_ids=["t3_reddit1", "12345678"]  # Mixed: Reddit + HN
        )
        db_session.add(pain_point)
        db_session.commit()

        # Verify JSONB array structure
        assert isinstance(pain_point.source_post_ids, list)
        assert len(pain_point.source_post_ids) == 2
        assert "t3_reddit1" in pain_point.source_post_ids
        assert "12345678" in pain_point.source_post_ids

    def test_source_post_ids_required(self, db_session):
        """Test that source_post_ids is still required (not nullable)"""
        from app.models.pain_point import PainPoint
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user and search run
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)

        search_run = SearchRun(
            id=str(uuid.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="7days"
        )
        db_session.add(search_run)
        db_session.commit()

        # Try to create without source_post_ids
        pain_point = PainPoint(
            search_run_id=search_run.id,
            extracted_text="Missing source IDs",
            relevance_score=0.5,
            sentiment_score=0.0,
            source_platform="reddit"
            # source_post_ids intentionally omitted
        )
        db_session.add(pain_point)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_query_pain_points_by_source_platform(self, db_session):
        """Test filtering pain points by source platform"""
        from app.models.pain_point import PainPoint
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user and search run
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)

        search_run = SearchRun(
            id=str(uuid.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="7days"
        )
        db_session.add(search_run)
        db_session.commit()

        # Create Reddit pain points
        for i in range(3):
            pain_point = PainPoint(
                search_run_id=search_run.id,
                extracted_text=f"Reddit pain point {i}",
                relevance_score=0.8,
                sentiment_score=-0.3,
                source_platform="reddit",
                source_post_ids=[f"t3_reddit{i}"]
            )
            db_session.add(pain_point)

        # Create HackerNews pain points
        for i in range(2):
            pain_point = PainPoint(
                search_run_id=search_run.id,
                extracted_text=f"HN pain point {i}",
                relevance_score=0.9,
                sentiment_score=-0.4,
                source_platform="hackernews",
                source_post_ids=[f"hn{i}"]
            )
            db_session.add(pain_point)

        db_session.commit()

        # Query by source platform
        reddit_points = db_session.query(PainPoint).filter_by(source_platform="reddit").all()
        hn_points = db_session.query(PainPoint).filter_by(source_platform="hackernews").all()

        assert len(reddit_points) == 3
        assert len(hn_points) == 2
        assert all(pp.source_platform == "reddit" for pp in reddit_points)
        assert all(pp.source_platform == "hackernews" for pp in hn_points)

    def test_backward_compatibility_with_existing_pain_points(self, db_session):
        """Test that existing pain points get default 'reddit' source_platform"""
        from app.models.pain_point import PainPoint
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Simulate existing pain point (pre-migration)
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)

        search_run = SearchRun(
            id=str(uuid.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="7days"
        )
        db_session.add(search_run)
        db_session.commit()

        # Old style pain point (would have been created before migration)
        pain_point = PainPoint(
            search_run_id=search_run.id,
            extracted_text="Legacy pain point",
            relevance_score=0.7,
            sentiment_score=-0.1,
            source_post_ids=["t3_legacy"]
            # source_platform not specified
        )
        db_session.add(pain_point)
        db_session.commit()

        # Re-fetch to verify default
        db_session.expunge_all()
        retrieved = db_session.query(PainPoint).filter_by(
            extracted_text="Legacy pain point"
        ).first()

        assert retrieved.source_platform == "reddit"

    def test_source_platform_max_length(self, db_session):
        """Test that source_platform has a max length of 20 characters"""
        from app.models.pain_point import PainPoint
        from app.models.search_run import SearchRun
        from app.models.user import User

        # Create user and search run
        user = User(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        db_session.add(user)

        search_run = SearchRun(
            id=str(uuid.uuid4()),
            user_id=user.id,
            status="completed",
            time_range="7days"
        )
        db_session.add(search_run)
        db_session.commit()

        # Try to create with source_platform > 20 chars
        pain_point = PainPoint(
            search_run_id=search_run.id,
            extracted_text="Long source platform test",
            relevance_score=0.5,
            sentiment_score=0.0,
            source_platform="this_is_longer_than_twenty_characters",
            source_post_ids=["test123"]
        )
        db_session.add(pain_point)

        with pytest.raises(Exception):  # DataError or similar
            db_session.commit()

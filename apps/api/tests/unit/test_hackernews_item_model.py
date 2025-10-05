"""
T005: Unit tests for HackerNewsItem model
Tests 48h cache behavior, validation, and expiry logic
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import uuid


class TestHackerNewsItemModel:
    """Unit tests for HackerNewsItem model"""

    def test_create_hackernews_item_with_all_fields(self, db_session):
        """Test creating HackerNewsItem with all fields populated"""
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()
        expires = now + timedelta(hours=48)

        item = HackerNewsItem(
            hn_id="12345678",
            hn_type="story",
            author="pg",
            title="Ask HN: Best tool for task management?",
            text="Looking for recommendations on task management tools",
            url="https://example.com/tool",
            hn_url="https://news.ycombinator.com/item?id=12345678",
            points=150,
            comment_count=45,
            created_utc=now,
            expires_at=expires,
            tags={"category": "ask_hn", "topic": "productivity"}
        )

        db_session.add(item)
        db_session.commit()

        # Verify all fields
        assert item.id is not None
        assert item.hn_id == "12345678"
        assert item.hn_type == "story"
        assert item.author == "pg"
        assert item.title == "Ask HN: Best tool for task management?"
        assert item.text == "Looking for recommendations on task management tools"
        assert item.url == "https://example.com/tool"
        assert item.hn_url == "https://news.ycombinator.com/item?id=12345678"
        assert item.points == 150
        assert item.comment_count == 45
        assert item.created_utc == now
        assert item.fetched_at is not None
        assert item.expires_at == expires
        assert item.tags == {"category": "ask_hn", "topic": "productivity"}

    def test_create_hackernews_item_minimal_fields(self, db_session):
        """Test creating HackerNewsItem with only required fields"""
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()
        expires = now + timedelta(hours=48)

        item = HackerNewsItem(
            hn_id="87654321",
            hn_type="comment",
            title="Great insight!",
            hn_url="https://news.ycombinator.com/item?id=87654321",
            points=0,
            comment_count=0,
            created_utc=now,
            expires_at=expires
        )

        db_session.add(item)
        db_session.commit()

        # Verify required fields
        assert item.hn_id == "87654321"
        assert item.hn_type == "comment"
        assert item.author is None
        assert item.text is None
        assert item.url is None
        assert item.tags is None

    def test_hn_id_uniqueness_constraint(self, db_session):
        """Test that hn_id must be unique"""
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()
        expires = now + timedelta(hours=48)

        # Create first item
        item1 = HackerNewsItem(
            hn_id="duplicate123",
            hn_type="story",
            title="First item",
            hn_url="https://news.ycombinator.com/item?id=duplicate123",
            points=10,
            comment_count=5,
            created_utc=now,
            expires_at=expires
        )
        db_session.add(item1)
        db_session.commit()

        # Try to create duplicate
        item2 = HackerNewsItem(
            hn_id="duplicate123",
            hn_type="story",
            title="Second item",
            hn_url="https://news.ycombinator.com/item?id=duplicate123",
            points=20,
            comment_count=10,
            created_utc=now,
            expires_at=expires
        )
        db_session.add(item2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_points_check_constraint_positive(self, db_session):
        """Test that points must be >= 0"""
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()
        expires = now + timedelta(hours=48)

        item = HackerNewsItem(
            hn_id="negative_points",
            hn_type="story",
            title="Test",
            hn_url="https://news.ycombinator.com/item?id=negative_points",
            points=-5,
            comment_count=0,
            created_utc=now,
            expires_at=expires
        )
        db_session.add(item)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_comment_count_check_constraint_positive(self, db_session):
        """Test that comment_count must be >= 0"""
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()
        expires = now + timedelta(hours=48)

        item = HackerNewsItem(
            hn_id="negative_comments",
            hn_type="story",
            title="Test",
            hn_url="https://news.ycombinator.com/item?id=negative_comments",
            points=10,
            comment_count=-3,
            created_utc=now,
            expires_at=expires
        )
        db_session.add(item)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_fetched_at_auto_set(self, db_session):
        """Test that fetched_at is automatically set to current time"""
        from app.models.hackernews_item import HackerNewsItem

        before = datetime.utcnow()

        item = HackerNewsItem(
            hn_id="auto_fetch",
            hn_type="story",
            title="Test",
            hn_url="https://news.ycombinator.com/item?id=auto_fetch",
            points=0,
            comment_count=0,
            created_utc=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=48)
        )
        db_session.add(item)
        db_session.commit()

        after = datetime.utcnow()

        # fetched_at should be between before and after
        assert before <= item.fetched_at <= after

    def test_48_hour_expiry_calculation(self, db_session):
        """Test 48-hour TTL expiry logic"""
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()
        expires_at = now + timedelta(hours=48)

        item = HackerNewsItem(
            hn_id="expiry_test",
            hn_type="story",
            title="Test",
            hn_url="https://news.ycombinator.com/item?id=expiry_test",
            points=0,
            comment_count=0,
            created_utc=now,
            expires_at=expires_at
        )
        db_session.add(item)
        db_session.commit()

        # Verify expiry is exactly 48 hours from now
        expected_delta = timedelta(hours=48)
        actual_delta = item.expires_at - now

        # Allow 1 second tolerance for test execution time
        assert abs(actual_delta - expected_delta) < timedelta(seconds=1)

    def test_is_expired_property(self, db_session):
        """Test is_expired property for TTL checking"""
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        # Create expired item
        expired_item = HackerNewsItem(
            hn_id="expired",
            hn_type="story",
            title="Expired",
            hn_url="https://news.ycombinator.com/item?id=expired",
            points=0,
            comment_count=0,
            created_utc=now - timedelta(hours=50),
            expires_at=now - timedelta(hours=2)
        )
        db_session.add(expired_item)

        # Create valid item
        valid_item = HackerNewsItem(
            hn_id="valid",
            hn_type="story",
            title="Valid",
            hn_url="https://news.ycombinator.com/item?id=valid",
            points=0,
            comment_count=0,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )
        db_session.add(valid_item)
        db_session.commit()

        assert expired_item.is_expired is True
        assert valid_item.is_expired is False

    def test_jsonb_tags_storage(self, db_session):
        """Test JSONB tags column stores complex structures"""
        from app.models.hackernews_item import HackerNewsItem

        complex_tags = {
            "topics": ["productivity", "tools", "apps"],
            "sentiment": {"score": 0.8, "label": "positive"},
            "meta": {
                "extracted_by": "worker-1",
                "confidence": 0.95
            }
        }

        item = HackerNewsItem(
            hn_id="jsonb_test",
            hn_type="story",
            title="Test",
            hn_url="https://news.ycombinator.com/item?id=jsonb_test",
            points=0,
            comment_count=0,
            created_utc=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=48),
            tags=complex_tags
        )
        db_session.add(item)
        db_session.commit()

        # Re-fetch to verify persistence
        db_session.expunge_all()
        retrieved = db_session.query(HackerNewsItem).filter_by(hn_id="jsonb_test").first()

        assert retrieved.tags == complex_tags
        assert retrieved.tags["topics"] == ["productivity", "tools", "apps"]
        assert retrieved.tags["sentiment"]["score"] == 0.8

    def test_index_on_hn_id(self, db_session):
        """Test that hn_id has an index for fast lookups"""
        from app.models.hackernews_item import HackerNewsItem
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        indexes = inspector.get_indexes('hackernews_items')

        # Find index on hn_id column
        hn_id_indexes = [idx for idx in indexes if 'hn_id' in idx['column_names']]

        assert len(hn_id_indexes) > 0, "No index found on hn_id column"

    def test_index_on_expires_at(self, db_session):
        """Test that expires_at has an index for TTL cleanup queries"""
        from app.models.hackernews_item import HackerNewsItem
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        indexes = inspector.get_indexes('hackernews_items')

        # Find index on expires_at column
        expires_indexes = [idx for idx in indexes if 'expires_at' in idx['column_names']]

        assert len(expires_indexes) > 0, "No index found on expires_at column"

    def test_index_on_created_utc(self, db_session):
        """Test that created_utc has an index for time-range queries"""
        from app.models.hackernews_item import HackerNewsItem
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        indexes = inspector.get_indexes('hackernews_items')

        # Find index on created_utc column
        created_indexes = [idx for idx in indexes if 'created_utc' in idx['column_names']]

        assert len(created_indexes) > 0, "No index found on created_utc column"

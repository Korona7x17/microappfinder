"""
T008: Unit tests for HackerNews fetch service
Tests Algolia API integration, 48h cache, and error handling
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import httpx


class TestHackerNewsFetchService:
    """Unit tests for HackerNews fetch service"""

    @patch('httpx.get')
    def test_fetch_hn_stories_from_algolia(self, mock_get, db_session):
        """Test fetching HN stories via Algolia API"""
        from app.services.hackernews_service import HackerNewsService

        # Mock Algolia API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hits": [
                {
                    "objectID": "12345678",
                    "title": "Ask HN: Best productivity tool?",
                    "author": "pg",
                    "points": 150,
                    "num_comments": 45,
                    "created_at_i": int(datetime.utcnow().timestamp()),
                    "url": None,
                    "story_text": "Looking for recommendations"
                }
            ]
        }
        mock_get.return_value = mock_response

        service = HackerNewsService(db_session)
        results = service.fetch_stories(
            query="productivity tool",
            tags="ask_hn"
        )

        assert len(results) == 1
        assert results[0]["hn_id"] == "12345678"
        assert results[0]["title"] == "Ask HN: Best productivity tool?"
        assert results[0]["points"] == 150

    @patch('httpx.get')
    def test_fetch_hn_items_stores_in_cache(self, mock_get, db_session):
        """Test that fetched HN items are stored in 48h cache"""
        from app.services.hackernews_service import HackerNewsService
        from app.models.hackernews_item import HackerNewsItem

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hits": [
                {
                    "objectID": "cached123",
                    "title": "Test Story",
                    "author": "tester",
                    "points": 10,
                    "num_comments": 5,
                    "created_at_i": int(datetime.utcnow().timestamp()),
                    "url": "https://example.com"
                }
            ]
        }
        mock_get.return_value = mock_response

        service = HackerNewsService(db_session)
        service.fetch_and_cache_stories(query="test")

        # Verify item in cache
        cached_item = db_session.query(HackerNewsItem).filter_by(
            hn_id="cached123"
        ).first()

        assert cached_item is not None
        assert cached_item.title == "Test Story"
        assert cached_item.expires_at > datetime.utcnow()

    def test_cache_deduplication_on_refetch(self, db_session):
        """Test that refetching same HN item uses cache"""
        from app.services.hackernews_service import HackerNewsService
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        # Create existing cached item
        existing_item = HackerNewsItem(
            hn_id="duplicate123",
            hn_type="story",
            title="Original Title",
            hn_url="https://news.ycombinator.com/item?id=duplicate123",
            points=100,
            comment_count=20,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )
        db_session.add(existing_item)
        db_session.commit()

        service = HackerNewsService(db_session)

        # Try to fetch same item
        cached = service.get_cached_item("duplicate123")

        assert cached is not None
        assert cached.hn_id == "duplicate123"
        assert cached.title == "Original Title"

    def test_expired_cache_items_refetched(self, db_session):
        """Test that expired cache items are refetched from API"""
        from app.services.hackernews_service import HackerNewsService
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        # Create expired item
        expired_item = HackerNewsItem(
            hn_id="expired123",
            hn_type="story",
            title="Expired Story",
            hn_url="https://news.ycombinator.com/item?id=expired123",
            points=50,
            comment_count=10,
            created_utc=now - timedelta(hours=50),
            expires_at=now - timedelta(hours=2)
        )
        db_session.add(expired_item)
        db_session.commit()

        service = HackerNewsService(db_session)

        # Check if item is expired
        assert expired_item.is_expired is True

        # get_cached_item should return None for expired items
        cached = service.get_cached_item("expired123")
        assert cached is None

    @patch('httpx.get')
    def test_algolia_api_error_handling(self, mock_get, db_session):
        """Test error handling for Algolia API failures"""
        from app.services.hackernews_service import HackerNewsService

        # Mock API error
        mock_get.side_effect = httpx.HTTPError("API Error")

        service = HackerNewsService(db_session)

        with pytest.raises(Exception):  # Should raise appropriate exception
            service.fetch_stories(query="test")

    @patch('httpx.get')
    def test_filter_ask_hn_posts(self, mock_get, db_session):
        """Test filtering for Ask HN posts specifically"""
        from app.services.hackernews_service import HackerNewsService

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hits": [
                {
                    "objectID": "ask123",
                    "title": "Ask HN: How to build SaaS?",
                    "author": "founder",
                    "points": 200,
                    "num_comments": 80,
                    "created_at_i": int(datetime.utcnow().timestamp())
                }
            ]
        }
        mock_get.return_value = mock_response

        service = HackerNewsService(db_session)
        results = service.fetch_stories(
            query="SaaS",
            tags="ask_hn"
        )

        # Verify Ask HN filter was applied
        assert len(results) == 1
        assert "Ask HN" in results[0]["title"]

    @patch('httpx.get')
    def test_minimum_points_threshold_filter(self, mock_get, db_session):
        """Test filtering HN items by minimum points threshold"""
        from app.services.hackernews_service import HackerNewsService

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hits": [
                {"objectID": "high", "title": "High Points", "points": 100, "num_comments": 50, "created_at_i": int(datetime.utcnow().timestamp())},
                {"objectID": "low", "title": "Low Points", "points": 2, "num_comments": 1, "created_at_i": int(datetime.utcnow().timestamp())}
            ]
        }
        mock_get.return_value = mock_response

        service = HackerNewsService(db_session)
        results = service.fetch_stories(
            query="test",
            min_points=10
        )

        # Should only return items with >= 10 points
        assert len(results) == 1
        assert results[0]["hn_id"] == "high"

    @patch('httpx.get')
    def test_time_range_filter(self, mock_get, db_session):
        """Test filtering HN items by time range"""
        from app.services.hackernews_service import HackerNewsService

        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hits": [
                {
                    "objectID": "recent",
                    "title": "Recent Post",
                    "points": 50,
                    "num_comments": 20,
                    "created_at_i": int((now - timedelta(days=2)).timestamp())
                },
                {
                    "objectID": "old",
                    "title": "Old Post",
                    "points": 100,
                    "num_comments": 40,
                    "created_at_i": int((now - timedelta(days=30)).timestamp())
                }
            ]
        }
        mock_get.return_value = mock_response

        service = HackerNewsService(db_session)
        results = service.fetch_stories(
            query="test",
            days_back=7
        )

        # Should only return items from last 7 days
        assert len(results) == 1
        assert results[0]["hn_id"] == "recent"

    @patch('httpx.get')
    def test_pagination_support(self, mock_get, db_session):
        """Test pagination when fetching HN stories"""
        from app.services.hackernews_service import HackerNewsService

        # Mock first page
        mock_response_page1 = Mock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            "hits": [
                {"objectID": f"story{i}", "title": f"Story {i}", "points": 10, "num_comments": 5, "created_at_i": int(datetime.utcnow().timestamp())}
                for i in range(20)
            ],
            "nbPages": 3
        }

        mock_get.return_value = mock_response_page1

        service = HackerNewsService(db_session)
        results = service.fetch_stories(
            query="test",
            page=0,
            per_page=20
        )

        assert len(results) == 20
        assert results[0]["hn_id"] == "story0"

    @patch('httpx.get')
    def test_extract_comments_from_story(self, mock_get, db_session):
        """Test extracting comments from HN story"""
        from app.services.hackernews_service import HackerNewsService

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "12345",
            "title": "Ask HN: Tools?",
            "children": [
                {"id": "comment1", "text": "I use Notion", "author": "user1"},
                {"id": "comment2", "text": "Try Obsidian", "author": "user2"}
            ]
        }
        mock_get.return_value = mock_response

        service = HackerNewsService(db_session)
        comments = service.fetch_comments("12345")

        assert len(comments) >= 2

    def test_cache_cleanup_removes_expired_items(self, db_session):
        """Test cleanup job removes expired cache items"""
        from app.services.hackernews_service import HackerNewsService
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        # Create mix of valid and expired items
        expired = HackerNewsItem(
            hn_id="expired",
            hn_type="story",
            title="Expired",
            hn_url="https://news.ycombinator.com/item?id=expired",
            points=10,
            comment_count=5,
            created_utc=now - timedelta(hours=50),
            expires_at=now - timedelta(hours=2)
        )
        valid = HackerNewsItem(
            hn_id="valid",
            hn_type="story",
            title="Valid",
            hn_url="https://news.ycombinator.com/item?id=valid",
            points=20,
            comment_count=10,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )
        db_session.add_all([expired, valid])
        db_session.commit()

        # Run cleanup
        service = HackerNewsService(db_session)
        deleted_count = service.cleanup_expired_cache()

        # Verify expired removed, valid remains
        assert deleted_count == 1
        assert db_session.query(HackerNewsItem).filter_by(hn_id="expired").first() is None
        assert db_session.query(HackerNewsItem).filter_by(hn_id="valid").first() is not None

    @patch('httpx.get')
    def test_rate_limit_handling(self, mock_get, db_session):
        """Test handling of Algolia rate limits (should not occur, but defensive)"""
        from app.services.hackernews_service import HackerNewsService

        # Mock 429 rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_get.return_value = mock_response

        service = HackerNewsService(db_session)

        with pytest.raises(Exception):  # Should handle rate limit appropriately
            service.fetch_stories(query="test")

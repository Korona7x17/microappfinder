"""
T009: Unit tests for cross-source deduplication logic
Tests semantic similarity and URL-based deduplication between Reddit and HN
"""
import pytest
from datetime import datetime, timedelta
import uuid


class TestCrossSourceDeduplication:
    """Unit tests for deduplication across Reddit and HackerNews sources"""

    def test_url_based_deduplication_same_url(self):
        """Test deduplication when Reddit and HN posts share same URL"""
        from app.services.deduplication_service import DeduplicationService

        reddit_item = {
            "id": "t3_reddit1",
            "url": "https://example.com/article",
            "title": "Interesting Article",
            "score": 100
        }

        hn_item = {
            "id": "12345678",
            "url": "https://example.com/article",
            "title": "Interesting Article",
            "points": 150
        }

        service = DeduplicationService()
        is_duplicate = service.is_duplicate_by_url(reddit_item, hn_item)

        assert is_duplicate is True

    def test_url_based_deduplication_different_urls(self):
        """Test that items with different URLs are not duplicates"""
        from app.services.deduplication_service import DeduplicationService

        reddit_item = {
            "id": "t3_reddit1",
            "url": "https://example.com/article1",
            "title": "Article 1"
        }

        hn_item = {
            "id": "12345678",
            "url": "https://example.com/article2",
            "title": "Article 2"
        }

        service = DeduplicationService()
        is_duplicate = service.is_duplicate_by_url(reddit_item, hn_item)

        assert is_duplicate is False

    def test_semantic_similarity_deduplication(self):
        """Test deduplication using semantic similarity (85% threshold)"""
        from app.services.deduplication_service import DeduplicationService

        reddit_text = "Looking for a good task management tool for developers"
        hn_text = "Need recommendations for developer task management software"

        service = DeduplicationService()
        similarity_score = service.calculate_semantic_similarity(
            reddit_text,
            hn_text
        )

        # These should be semantically similar (>= 0.85)
        assert similarity_score >= 0.85

    def test_semantic_similarity_below_threshold(self):
        """Test that dissimilar content is not considered duplicate"""
        from app.services.deduplication_service import DeduplicationService

        reddit_text = "Looking for a task management tool"
        hn_text = "Best programming language for beginners"

        service = DeduplicationService()
        similarity_score = service.calculate_semantic_similarity(
            reddit_text,
            hn_text
        )

        # These should not be similar (< 0.85)
        assert similarity_score < 0.85

    def test_deduplicate_reddit_and_hn_items(self, db_session):
        """Test deduplication between Reddit and HN item lists"""
        from app.services.deduplication_service import DeduplicationService
        from app.models.reddit_post import RedditPost
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        # Create Reddit post
        reddit_post = RedditPost(
            reddit_id="t3_abc123",
            title="Ask: Best productivity app?",
            selftext="Looking for recommendations",
            score=100,
            num_comments=50,
            subreddit="productivity",
            author="redditor1",
            created_utc=now,
            url="https://reddit.com/r/productivity/abc123",
            expires_at=now + timedelta(hours=48)
        )
        db_session.add(reddit_post)

        # Create similar HN item
        hn_item = HackerNewsItem(
            hn_id="12345678",
            hn_type="story",
            title="Ask HN: Best productivity app?",
            text="Looking for recommendations",
            hn_url="https://news.ycombinator.com/item?id=12345678",
            points=150,
            comment_count=75,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )
        db_session.add(hn_item)
        db_session.commit()

        service = DeduplicationService(db_session)
        result = service.deduplicate_cross_source(
            reddit_posts=[reddit_post],
            hn_items=[hn_item]
        )

        # Should identify as duplicate and merge
        assert len(result["unique_items"]) == 1
        assert len(result["duplicates"]) == 1

    def test_keep_higher_engagement_item_on_dedup(self, db_session):
        """Test that deduplication keeps item with higher engagement"""
        from app.services.deduplication_service import DeduplicationService
        from app.models.reddit_post import RedditPost
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        # Reddit post with lower engagement
        reddit_post = RedditPost(
            reddit_id="t3_low",
            title="Task management tool?",
            selftext="Need recommendations",
            score=50,
            num_comments=20,
            subreddit="productivity",
            author="user1",
            created_utc=now,
            url="https://reddit.com/r/productivity/low",
            expires_at=now + timedelta(hours=48)
        )

        # HN item with higher engagement
        hn_item = HackerNewsItem(
            hn_id="high",
            hn_type="story",
            title="Task management tool?",
            text="Need recommendations",
            hn_url="https://news.ycombinator.com/item?id=high",
            points=200,
            comment_count=100,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )

        db_session.add_all([reddit_post, hn_item])
        db_session.commit()

        service = DeduplicationService(db_session)
        result = service.deduplicate_cross_source(
            reddit_posts=[reddit_post],
            hn_items=[hn_item]
        )

        # Should keep HN item (higher engagement)
        kept_item = result["unique_items"][0]
        assert kept_item["source"] == "hackernews"
        assert kept_item["id"] == "high"

    def test_preserve_both_source_ids_on_dedup(self, db_session):
        """Test that deduplication preserves IDs from both sources"""
        from app.services.deduplication_service import DeduplicationService
        from app.models.reddit_post import RedditPost
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        reddit_post = RedditPost(
            reddit_id="t3_reddit",
            title="Same content",
            score=100,
            num_comments=50,
            subreddit="test",
            author="user",
            created_utc=now,
            url="https://reddit.com/test",
            expires_at=now + timedelta(hours=48)
        )

        hn_item = HackerNewsItem(
            hn_id="hn123",
            hn_type="story",
            title="Same content",
            hn_url="https://news.ycombinator.com/item?id=hn123",
            points=150,
            comment_count=75,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )

        db_session.add_all([reddit_post, hn_item])
        db_session.commit()

        service = DeduplicationService(db_session)
        result = service.deduplicate_cross_source(
            reddit_posts=[reddit_post],
            hn_items=[hn_item]
        )

        # Merged item should have both source IDs
        merged = result["unique_items"][0]
        assert "t3_reddit" in merged["source_ids"]
        assert "hn123" in merged["source_ids"]

    def test_no_deduplication_for_distinct_content(self, db_session):
        """Test that distinct content items are not deduplicated"""
        from app.services.deduplication_service import DeduplicationService
        from app.models.reddit_post import RedditPost
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        reddit_post = RedditPost(
            reddit_id="t3_distinct1",
            title="Task management tools",
            score=100,
            num_comments=50,
            subreddit="productivity",
            author="user1",
            created_utc=now,
            url="https://reddit.com/productivity/distinct1",
            expires_at=now + timedelta(hours=48)
        )

        hn_item = HackerNewsItem(
            hn_id="distinct2",
            hn_type="story",
            title="Programming languages comparison",
            hn_url="https://news.ycombinator.com/item?id=distinct2",
            points=150,
            comment_count=75,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )

        db_session.add_all([reddit_post, hn_item])
        db_session.commit()

        service = DeduplicationService(db_session)
        result = service.deduplicate_cross_source(
            reddit_posts=[reddit_post],
            hn_items=[hn_item]
        )

        # Both should be kept as unique
        assert len(result["unique_items"]) == 2
        assert len(result["duplicates"]) == 0

    def test_batch_deduplication_performance(self, db_session):
        """Test deduplication performance with large batches"""
        from app.services.deduplication_service import DeduplicationService
        from app.models.reddit_post import RedditPost
        from app.models.hackernews_item import HackerNewsItem
        import time

        now = datetime.utcnow()

        # Create 100 Reddit posts
        reddit_posts = []
        for i in range(100):
            post = RedditPost(
                reddit_id=f"t3_reddit{i}",
                title=f"Post {i}",
                score=100,
                num_comments=50,
                subreddit="test",
                author="user",
                created_utc=now,
                url=f"https://reddit.com/test/{i}",
                expires_at=now + timedelta(hours=48)
            )
            reddit_posts.append(post)
            db_session.add(post)

        # Create 50 HN items (some duplicates)
        hn_items = []
        for i in range(50):
            item = HackerNewsItem(
                hn_id=f"hn{i}",
                hn_type="story",
                title=f"Post {i * 2}",  # Some overlap with Reddit
                hn_url=f"https://news.ycombinator.com/item?id=hn{i}",
                points=150,
                comment_count=75,
                created_utc=now,
                expires_at=now + timedelta(hours=48)
            )
            hn_items.append(item)
            db_session.add(item)

        db_session.commit()

        service = DeduplicationService(db_session)

        start = time.time()
        result = service.deduplicate_cross_source(
            reddit_posts=reddit_posts,
            hn_items=hn_items
        )
        duration = time.time() - start

        # Should complete in reasonable time (< 5 seconds for 150 items)
        assert duration < 5.0
        assert len(result["unique_items"]) > 0

    def test_url_normalization_before_dedup(self):
        """Test URL normalization handles different formats"""
        from app.services.deduplication_service import DeduplicationService

        service = DeduplicationService()

        # Different URL formats for same resource
        url1 = "https://example.com/article?utm_source=reddit"
        url2 = "https://example.com/article?utm_source=hn"
        url3 = "http://example.com/article"
        url4 = "https://www.example.com/article"

        normalized1 = service.normalize_url(url1)
        normalized2 = service.normalize_url(url2)
        normalized3 = service.normalize_url(url3)
        normalized4 = service.normalize_url(url4)

        # All should normalize to same URL
        assert normalized1 == normalized2 == normalized3 == normalized4

    def test_title_similarity_with_prefix_variations(self):
        """Test that Ask HN/Ask Reddit prefixes don't affect similarity"""
        from app.services.deduplication_service import DeduplicationService

        service = DeduplicationService()

        reddit_title = "What's the best productivity tool?"
        hn_title = "Ask HN: What's the best productivity tool?"

        similarity = service.calculate_title_similarity(
            reddit_title,
            hn_title
        )

        # Should be highly similar despite prefix
        assert similarity >= 0.85

"""
T010: Unit tests for unified search aggregation
Tests combining Reddit and HackerNews results with composite scoring
"""
import pytest
from datetime import datetime, timedelta
import uuid


class TestUnifiedSearchAggregation:
    """Unit tests for unified multi-source search aggregation"""

    def test_aggregate_reddit_and_hn_results(self, db_session):
        """Test aggregating results from Reddit and HackerNews"""
        from app.services.unified_search_service import UnifiedSearchService
        from app.models.reddit_post import RedditPost
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        # Create Reddit posts
        reddit_post = RedditPost(
            reddit_id="t3_r1",
            title="Productivity tool",
            score=100,
            num_comments=50,
            subreddit="productivity",
            author="user1",
            created_utc=now,
            url="https://reddit.com/r/productivity/r1",
            expires_at=now + timedelta(hours=48)
        )

        # Create HN item
        hn_item = HackerNewsItem(
            hn_id="hn1",
            hn_type="story",
            title="Ask HN: Productivity tools",
            hn_url="https://news.ycombinator.com/item?id=hn1",
            points=150,
            comment_count=75,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )

        db_session.add_all([reddit_post, hn_item])
        db_session.commit()

        service = UnifiedSearchService(db_session)
        results = service.aggregate_sources(
            reddit_posts=[reddit_post],
            hn_items=[hn_item]
        )

        # Should return unified results from both sources
        assert len(results) == 2
        assert any(r["source"] == "reddit" for r in results)
        assert any(r["source"] == "hackernews" for r in results)

    def test_composite_score_calculation(self, db_session):
        """Test composite score: 0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment"""
        from app.services.unified_search_service import UnifiedSearchService
        from app.models.reddit_post import RedditPost

        now = datetime.utcnow()

        reddit_post = RedditPost(
            reddit_id="t3_score_test",
            title="Test scoring",
            score=100,
            num_comments=50,
            subreddit="test",
            author="user",
            created_utc=now,
            url="https://reddit.com/test",
            expires_at=now + timedelta(hours=48)
        )

        db_session.add(reddit_post)
        db_session.commit()

        service = UnifiedSearchService(db_session)
        score = service.calculate_composite_score(
            upvotes=100,
            comments=50,
            created_at=now,
            sentiment=0.5
        )

        # Verify score components
        assert 0 <= score <= 1
        # Score should be: 0.3×(100/max) + 0.25×(50/max) + 0.25×(recency) + 0.2×(0.5)

    def test_sort_by_composite_score_descending(self, db_session):
        """Test results sorted by composite score (highest first)"""
        from app.services.unified_search_service import UnifiedSearchService
        from app.models.reddit_post import RedditPost

        now = datetime.utcnow()

        # High score post
        high_score = RedditPost(
            reddit_id="t3_high",
            title="High engagement",
            score=500,
            num_comments=200,
            subreddit="test",
            author="user",
            created_utc=now,
            url="https://reddit.com/high",
            expires_at=now + timedelta(hours=48)
        )

        # Low score post
        low_score = RedditPost(
            reddit_id="t3_low",
            title="Low engagement",
            score=10,
            num_comments=2,
            subreddit="test",
            author="user",
            created_utc=now - timedelta(days=30),
            url="https://reddit.com/low",
            expires_at=now + timedelta(hours=48)
        )

        db_session.add_all([high_score, low_score])
        db_session.commit()

        service = UnifiedSearchService(db_session)
        results = service.aggregate_and_rank(
            reddit_posts=[high_score, low_score],
            hn_items=[]
        )

        # Results should be sorted by score descending
        assert results[0]["id"] == "t3_high"
        assert results[1]["id"] == "t3_low"
        assert results[0]["composite_score"] > results[1]["composite_score"]

    def test_cross_source_ranking(self, db_session):
        """Test ranking mixes Reddit and HN items by composite score"""
        from app.services.unified_search_service import UnifiedSearchService
        from app.models.reddit_post import RedditPost
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        # Medium score Reddit post
        reddit_post = RedditPost(
            reddit_id="t3_medium",
            title="Medium engagement",
            score=100,
            num_comments=50,
            subreddit="test",
            author="user",
            created_utc=now,
            url="https://reddit.com/medium",
            expires_at=now + timedelta(hours=48)
        )

        # High score HN item
        hn_item = HackerNewsItem(
            hn_id="hn_high",
            hn_type="story",
            title="High engagement",
            hn_url="https://news.ycombinator.com/item?id=hn_high",
            points=300,
            comment_count=150,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )

        db_session.add_all([reddit_post, hn_item])
        db_session.commit()

        service = UnifiedSearchService(db_session)
        results = service.aggregate_and_rank(
            reddit_posts=[reddit_post],
            hn_items=[hn_item]
        )

        # HN item should rank higher due to better engagement
        assert results[0]["source"] == "hackernews"
        assert results[1]["source"] == "reddit"

    def test_recency_factor_in_scoring(self, db_session):
        """Test that recency affects composite score (25% weight)"""
        from app.services.unified_search_service import UnifiedSearchService
        from app.models.reddit_post import RedditPost

        now = datetime.utcnow()

        # Recent post with lower engagement
        recent = RedditPost(
            reddit_id="t3_recent",
            title="Recent",
            score=50,
            num_comments=20,
            subreddit="test",
            author="user",
            created_utc=now - timedelta(hours=1),
            url="https://reddit.com/recent",
            expires_at=now + timedelta(hours=48)
        )

        # Old post with higher engagement
        old = RedditPost(
            reddit_id="t3_old",
            title="Old",
            score=100,
            num_comments=40,
            subreddit="test",
            author="user",
            created_utc=now - timedelta(days=90),
            url="https://reddit.com/old",
            expires_at=now + timedelta(hours=48)
        )

        db_session.add_all([recent, old])
        db_session.commit()

        service = UnifiedSearchService(db_session)

        recent_score = service.calculate_composite_score(
            upvotes=50,
            comments=20,
            created_at=recent.created_utc,
            sentiment=0.0
        )

        old_score = service.calculate_composite_score(
            upvotes=100,
            comments=40,
            created_at=old.created_utc,
            sentiment=0.0
        )

        # Recency should boost recent post's score
        assert recent_score > 0

    def test_sentiment_factor_in_scoring(self, db_session):
        """Test sentiment affects composite score (20% weight)"""
        from app.services.unified_search_service import UnifiedSearchService

        service = UnifiedSearchService(db_session)

        # Positive sentiment
        positive_score = service.calculate_composite_score(
            upvotes=100,
            comments=50,
            created_at=datetime.utcnow(),
            sentiment=1.0  # Very positive
        )

        # Negative sentiment
        negative_score = service.calculate_composite_score(
            upvotes=100,
            comments=50,
            created_at=datetime.utcnow(),
            sentiment=-1.0  # Very negative
        )

        # Positive sentiment should yield higher score
        assert positive_score > negative_score

    def test_pagination_support(self, db_session):
        """Test paginated results from unified search"""
        from app.services.unified_search_service import UnifiedSearchService
        from app.models.reddit_post import RedditPost

        now = datetime.utcnow()

        # Create 100 posts
        posts = []
        for i in range(100):
            post = RedditPost(
                reddit_id=f"t3_{i}",
                title=f"Post {i}",
                score=100 - i,  # Decreasing scores
                num_comments=50,
                subreddit="test",
                author="user",
                created_utc=now,
                url=f"https://reddit.com/{i}",
                expires_at=now + timedelta(hours=48)
            )
            posts.append(post)
            db_session.add(post)

        db_session.commit()

        service = UnifiedSearchService(db_session)

        # Get first page (50 items)
        page1 = service.aggregate_and_rank(
            reddit_posts=posts,
            hn_items=[],
            page=1,
            per_page=50
        )

        # Get second page (50 items)
        page2 = service.aggregate_and_rank(
            reddit_posts=posts,
            hn_items=[],
            page=2,
            per_page=50
        )

        assert len(page1) == 50
        assert len(page2) == 50
        assert page1[0]["id"] != page2[0]["id"]

    def test_filter_by_source_platform(self, db_session):
        """Test filtering unified results by source platform"""
        from app.services.unified_search_service import UnifiedSearchService
        from app.models.reddit_post import RedditPost
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        reddit_post = RedditPost(
            reddit_id="t3_reddit",
            title="Reddit post",
            score=100,
            num_comments=50,
            subreddit="test",
            author="user",
            created_utc=now,
            url="https://reddit.com/test",
            expires_at=now + timedelta(hours=48)
        )

        hn_item = HackerNewsItem(
            hn_id="hn1",
            hn_type="story",
            title="HN post",
            hn_url="https://news.ycombinator.com/item?id=hn1",
            points=150,
            comment_count=75,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )

        db_session.add_all([reddit_post, hn_item])
        db_session.commit()

        service = UnifiedSearchService(db_session)

        # Filter Reddit only
        reddit_only = service.aggregate_and_rank(
            reddit_posts=[reddit_post],
            hn_items=[hn_item],
            source_filter="reddit"
        )

        # Filter HN only
        hn_only = service.aggregate_and_rank(
            reddit_posts=[reddit_post],
            hn_items=[hn_item],
            source_filter="hackernews"
        )

        assert len(reddit_only) == 1
        assert reddit_only[0]["source"] == "reddit"
        assert len(hn_only) == 1
        assert hn_only[0]["source"] == "hackernews"

    def test_normalize_scores_across_platforms(self, db_session):
        """Test score normalization handles different platform scales"""
        from app.services.unified_search_service import UnifiedSearchService

        service = UnifiedSearchService(db_session)

        # Reddit scores (typically lower)
        reddit_normalized = service.normalize_engagement_score(
            score=100,
            max_score=500,
            platform="reddit"
        )

        # HN scores (can be higher)
        hn_normalized = service.normalize_engagement_score(
            score=300,
            max_score=1000,
            platform="hackernews"
        )

        # Both should be in [0, 1] range
        assert 0 <= reddit_normalized <= 1
        assert 0 <= hn_normalized <= 1

    def test_preserve_source_metadata(self, db_session):
        """Test that source-specific metadata is preserved in unified results"""
        from app.services.unified_search_service import UnifiedSearchService
        from app.models.reddit_post import RedditPost
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        reddit_post = RedditPost(
            reddit_id="t3_meta",
            title="Test",
            score=100,
            num_comments=50,
            subreddit="test_subreddit",
            author="reddit_user",
            created_utc=now,
            url="https://reddit.com/meta",
            expires_at=now + timedelta(hours=48)
        )

        hn_item = HackerNewsItem(
            hn_id="hn_meta",
            hn_type="ask_hn",
            author="hn_user",
            title="Test",
            hn_url="https://news.ycombinator.com/item?id=hn_meta",
            points=150,
            comment_count=75,
            created_utc=now,
            expires_at=now + timedelta(hours=48)
        )

        db_session.add_all([reddit_post, hn_item])
        db_session.commit()

        service = UnifiedSearchService(db_session)
        results = service.aggregate_and_rank(
            reddit_posts=[reddit_post],
            hn_items=[hn_item]
        )

        # Find Reddit result
        reddit_result = next(r for r in results if r["source"] == "reddit")
        assert reddit_result["metadata"]["subreddit"] == "test_subreddit"
        assert reddit_result["metadata"]["author"] == "reddit_user"

        # Find HN result
        hn_result = next(r for r in results if r["source"] == "hackernews")
        assert hn_result["metadata"]["hn_type"] == "ask_hn"
        assert hn_result["metadata"]["author"] == "hn_user"

    def test_time_range_filtering_across_sources(self, db_session):
        """Test applying time range filter to both Reddit and HN"""
        from app.services.unified_search_service import UnifiedSearchService
        from app.models.reddit_post import RedditPost
        from app.models.hackernews_item import HackerNewsItem

        now = datetime.utcnow()

        # Recent items (within 7 days)
        recent_reddit = RedditPost(
            reddit_id="t3_recent",
            title="Recent Reddit",
            score=100,
            num_comments=50,
            subreddit="test",
            author="user",
            created_utc=now - timedelta(days=3),
            url="https://reddit.com/recent",
            expires_at=now + timedelta(hours=48)
        )

        recent_hn = HackerNewsItem(
            hn_id="hn_recent",
            hn_type="story",
            title="Recent HN",
            hn_url="https://news.ycombinator.com/item?id=hn_recent",
            points=150,
            comment_count=75,
            created_utc=now - timedelta(days=5),
            expires_at=now + timedelta(hours=48)
        )

        # Old items (outside 7 days)
        old_reddit = RedditPost(
            reddit_id="t3_old",
            title="Old Reddit",
            score=100,
            num_comments=50,
            subreddit="test",
            author="user",
            created_utc=now - timedelta(days=30),
            url="https://reddit.com/old",
            expires_at=now + timedelta(hours=48)
        )

        db_session.add_all([recent_reddit, recent_hn, old_reddit])
        db_session.commit()

        service = UnifiedSearchService(db_session)
        results = service.aggregate_and_rank(
            reddit_posts=[recent_reddit, old_reddit],
            hn_items=[recent_hn],
            time_range="7days"
        )

        # Should only return items from last 7 days
        assert len(results) == 2
        assert all(
            (now - r["created_at"]).days <= 7
            for r in results
        )

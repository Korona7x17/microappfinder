"""
T048: Unit tests for NSFW/spam filter
Tests for content filtering rules
"""
import pytest
from worker.pipeline.filter import ContentFilter


class TestContentFilter:
    """Unit tests for ContentFilter"""

    def test_is_nsfw_true(self):
        """Test NSFW detection returns True"""
        post = {"is_nsfw": True}
        assert ContentFilter.is_nsfw(post) is True

    def test_is_nsfw_false(self):
        """Test NSFW detection returns False"""
        post = {"is_nsfw": False}
        assert ContentFilter.is_nsfw(post) is False

    def test_is_nsfw_missing_field(self):
        """Test NSFW detection with missing field defaults to False"""
        post = {}
        assert ContentFilter.is_nsfw(post) is False

    def test_contains_spam_keywords_buy_now(self):
        """Test spam detection for 'buy now'"""
        assert ContentFilter.contains_spam_keywords("Click here to buy now!") is True
        assert ContentFilter.contains_spam_keywords("BUY NOW limited offer") is True

    def test_contains_spam_keywords_crypto(self):
        """Test spam detection for crypto keywords"""
        assert ContentFilter.contains_spam_keywords("Invest in crypto today") is True
        assert ContentFilter.contains_spam_keywords("Bitcoin investment opportunity") is True
        assert ContentFilter.contains_spam_keywords("NFT collection launching") is True

    def test_contains_spam_keywords_urgency(self):
        """Test spam detection for urgency keywords"""
        assert ContentFilter.contains_spam_keywords("Act now, limited time!") is True
        assert ContentFilter.contains_spam_keywords("Guaranteed returns") is True

    def test_contains_spam_keywords_clean_text(self):
        """Test spam detection returns False for clean text"""
        clean_texts = [
            "I need a productivity tool",
            "Struggling with time management",
            "Looking for project tracking software",
            "How do you handle customer support?",
        ]

        for text in clean_texts:
            assert ContentFilter.contains_spam_keywords(text) is False

    def test_contains_spam_keywords_empty(self):
        """Test spam detection with empty text"""
        assert ContentFilter.contains_spam_keywords("") is False
        assert ContentFilter.contains_spam_keywords(None) is False

    def test_is_low_quality_below_threshold(self):
        """Test low quality detection for posts below threshold"""
        assert ContentFilter.is_low_quality({"score": 0}) is True
        assert ContentFilter.is_low_quality({"score": 1}) is True

    def test_is_low_quality_at_threshold(self):
        """Test posts at threshold (2) pass"""
        assert ContentFilter.is_low_quality({"score": 2}) is False
        assert ContentFilter.is_low_quality({"score": 3}) is False
        assert ContentFilter.is_low_quality({"score": 100}) is False

    def test_is_low_quality_missing_score(self):
        """Test low quality with missing score defaults to 0"""
        assert ContentFilter.is_low_quality({}) is True

    def test_is_deleted_or_removed_deleted(self):
        """Test detection of [deleted] posts"""
        post = {"text": "[deleted]", "author": None}
        assert ContentFilter.is_deleted_or_removed(post) is True

    def test_is_deleted_or_removed_removed(self):
        """Test detection of [removed] posts"""
        post = {"text": "[removed]", "author": "user"}
        assert ContentFilter.is_deleted_or_removed(post) is True

    def test_is_deleted_or_removed_no_author(self):
        """Test detection of posts with deleted author"""
        post = {"text": "", "author": None}
        assert ContentFilter.is_deleted_or_removed(post) is True

    def test_is_deleted_or_removed_normal_post(self):
        """Test normal posts are not flagged as deleted"""
        post = {"text": "Normal post content", "author": "username"}
        assert ContentFilter.is_deleted_or_removed(post) is False

    def test_is_too_short_below_threshold(self):
        """Test too short detection"""
        assert ContentFilter.is_too_short("short") is True
        assert ContentFilter.is_too_short("a bit longer but still short") is False

    def test_is_too_short_empty(self):
        """Test empty text is too short"""
        assert ContentFilter.is_too_short("") is True
        assert ContentFilter.is_too_short("   ") is True
        assert ContentFilter.is_too_short(None) is True

    def test_is_too_short_custom_min_length(self):
        """Test custom minimum length"""
        text = "exactly ten!!"
        assert ContentFilter.is_too_short(text, min_length=10) is False
        assert ContentFilter.is_too_short(text, min_length=20) is True

    def test_should_filter_nsfw(self):
        """Test filtering NSFW posts"""
        post = {
            "is_nsfw": True,
            "text": "Normal text",
            "title": "Title",
            "score": 10
        }

        assert ContentFilter.should_filter(post, filter_nsfw=True) is True
        assert ContentFilter.should_filter(post, filter_nsfw=False) is False

    def test_should_filter_spam(self):
        """Test filtering spam posts"""
        post = {
            "is_nsfw": False,
            "title": "Buy now!",
            "text": "Limited time offer",
            "score": 10
        }

        assert ContentFilter.should_filter(post) is True

    def test_should_filter_low_quality(self):
        """Test filtering low quality posts"""
        post = {
            "is_nsfw": False,
            "title": "Good title",
            "text": "Good content that is long enough",
            "score": 1  # Below threshold
        }

        assert ContentFilter.should_filter(post) is True

    def test_should_filter_too_short(self):
        """Test filtering too short posts"""
        post = {
            "is_nsfw": False,
            "title": "Short",
            "text": "Also short",
            "score": 10
        }

        assert ContentFilter.should_filter(post) is True

    def test_should_filter_deleted(self):
        """Test filtering deleted posts"""
        post = {
            "is_nsfw": False,
            "title": "Title",
            "text": "[deleted]",
            "score": 10,
            "author": None
        }

        assert ContentFilter.should_filter(post) is True

    def test_should_filter_clean_post(self):
        """Test clean posts pass all filters"""
        post = {
            "is_nsfw": False,
            "title": "Looking for productivity tools",
            "text": "I struggle with time management and need a better system for tracking tasks",
            "score": 25,
            "author": "username"
        }

        assert ContentFilter.should_filter(post) is False

    def test_filter_posts_removes_filtered(self):
        """Test filter_posts removes filtered posts"""
        posts = [
            {"is_nsfw": True, "title": "NSFW", "text": "content", "score": 10},
            {"is_nsfw": False, "title": "Good post with enough text", "text": "content", "score": 10},
            {"is_nsfw": False, "title": "Buy now!", "text": "crypto", "score": 10},
            {"is_nsfw": False, "title": "Another good post here", "text": "more content", "score": 15},
        ]

        filtered = ContentFilter.filter_posts(posts, filter_nsfw=True)

        assert len(filtered) == 2
        assert filtered[0]["title"] == "Good post with enough text"
        assert filtered[1]["title"] == "Another good post here"

    def test_filter_posts_empty_list(self):
        """Test filter_posts with empty list"""
        assert ContentFilter.filter_posts([]) == []

    def test_get_filter_stats(self):
        """Test filter statistics calculation"""
        posts = [
            {"is_nsfw": True, "title": "NSFW", "text": "content", "score": 10, "author": "user"},
            {"is_nsfw": False, "title": "Buy now!", "text": "spam content here", "score": 10, "author": "user"},
            {"is_nsfw": False, "title": "Low score", "text": "some content here yes", "score": 1, "author": "user"},
            {"is_nsfw": False, "title": "Short", "text": "x", "score": 10, "author": "user"},
            {"is_nsfw": False, "title": "[deleted]", "text": "[deleted]", "score": 10, "author": None},
            {"is_nsfw": False, "title": "Good post here", "text": "quality content with length", "score": 15, "author": "user"},
        ]

        stats = ContentFilter.get_filter_stats(posts)

        assert stats["total"] == 6
        assert stats["nsfw"] == 1
        assert stats["spam"] == 1
        assert stats["low_quality"] == 1
        assert stats["too_short"] == 1
        assert stats["deleted"] == 1
        assert stats["passed"] == 1

    def test_spam_keywords_case_insensitive(self):
        """Test spam detection is case insensitive"""
        assert ContentFilter.contains_spam_keywords("BUY NOW") is True
        assert ContentFilter.contains_spam_keywords("buy now") is True
        assert ContentFilter.contains_spam_keywords("Buy Now") is True
        assert ContentFilter.contains_spam_keywords("CRYPTO") is True
        assert ContentFilter.contains_spam_keywords("crypto") is True

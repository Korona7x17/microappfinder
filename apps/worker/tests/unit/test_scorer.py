"""
T047: Unit tests for composite scorer
Tests for relevance score calculation and normalization
"""
import pytest
from datetime import datetime, timedelta
from worker.pipeline.scorer import CompositeScorer


class TestCompositeScorer:
    """Unit tests for CompositeScorer"""

    def test_normalize_upvotes_within_range(self):
        """Test upvote normalization for values within max range"""
        assert CompositeScorer.normalize_upvotes(0) == 0.0
        assert CompositeScorer.normalize_upvotes(500) == 0.5
        assert CompositeScorer.normalize_upvotes(1000) == 1.0

    def test_normalize_upvotes_above_max(self):
        """Test upvote normalization caps at 1.0"""
        assert CompositeScorer.normalize_upvotes(2000) == 1.0
        assert CompositeScorer.normalize_upvotes(5000) == 1.0

    def test_normalize_upvotes_negative(self):
        """Test negative upvotes return 0.0"""
        assert CompositeScorer.normalize_upvotes(-10) == 0.0
        assert CompositeScorer.normalize_upvotes(-100) == 0.0

    def test_normalize_comments_within_range(self):
        """Test comment normalization for values within max range"""
        assert CompositeScorer.normalize_comments(0) == 0.0
        assert CompositeScorer.normalize_comments(250) == 0.5
        assert CompositeScorer.normalize_comments(500) == 1.0

    def test_normalize_comments_above_max(self):
        """Test comment normalization caps at 1.0"""
        assert CompositeScorer.normalize_comments(1000) == 1.0
        assert CompositeScorer.normalize_comments(2000) == 1.0

    def test_normalize_recency_recent_post(self):
        """Test recency for very recent posts"""
        now = datetime.utcnow()
        assert CompositeScorer.normalize_recency(now) == 1.0

        # 1 day ago
        one_day_ago = now - timedelta(days=1)
        recency = CompositeScorer.normalize_recency(one_day_ago)
        assert 0.98 < recency <= 1.0  # Should be very high

    def test_normalize_recency_old_post(self):
        """Test recency for old posts"""
        now = datetime.utcnow()

        # 45 days ago (half of max age)
        mid_age = now - timedelta(days=45)
        recency = CompositeScorer.normalize_recency(mid_age)
        assert 0.45 < recency < 0.55  # Should be around 0.5

        # 90 days ago (max age)
        old = now - timedelta(days=90)
        recency = CompositeScorer.normalize_recency(old)
        assert recency == 0.0

        # Beyond max age
        very_old = now - timedelta(days=120)
        recency = CompositeScorer.normalize_recency(very_old)
        assert recency == 0.0

    def test_normalize_recency_future_timestamp(self):
        """Test recency handles future timestamps gracefully"""
        future = datetime.utcnow() + timedelta(days=1)
        assert CompositeScorer.normalize_recency(future) == 1.0

    def test_calculate_sentiment_negative_text(self):
        """Test sentiment calculation for negative/pain text"""
        negative_text = "I hate this tool, it's terrible and frustrating"
        sentiment = CompositeScorer.calculate_sentiment(negative_text)

        # Should be positive contribution (pain = negative polarity = inverted to positive)
        assert sentiment > 0

    def test_calculate_sentiment_positive_text(self):
        """Test sentiment calculation for positive text"""
        positive_text = "I love this amazing wonderful tool"
        sentiment = CompositeScorer.calculate_sentiment(positive_text)

        # Should be low/negative contribution (joy = positive polarity = inverted to negative)
        assert sentiment < 0

    def test_calculate_sentiment_neutral_text(self):
        """Test sentiment calculation for neutral text"""
        neutral_text = "This is a tool for managing tasks"
        sentiment = CompositeScorer.calculate_sentiment(neutral_text)

        # Should be close to 0
        assert -0.2 < sentiment < 0.2

    def test_calculate_sentiment_empty_text(self):
        """Test sentiment with empty text"""
        assert CompositeScorer.calculate_sentiment("") == 0.0
        assert CompositeScorer.calculate_sentiment("   ") == 0.0
        assert CompositeScorer.calculate_sentiment(None) == 0.0

    def test_calculate_composite_score_high_engagement(self):
        """Test composite score for high engagement post"""
        post_data = {
            "score": 1000,  # Max upvotes
            "comment_count": 500,  # Max comments
            "created_utc": datetime.utcnow(),  # Very recent
            "text": "I hate dealing with this problem every day"  # Pain
        }

        score = CompositeScorer.calculate_composite_score(post_data)

        # Should be high (all components at max)
        assert 0.8 < score <= 1.0

    def test_calculate_composite_score_low_engagement(self):
        """Test composite score for low engagement post"""
        post_data = {
            "score": 0,
            "comment_count": 0,
            "created_utc": datetime.utcnow() - timedelta(days=90),
            "text": "I love everything"  # Positive sentiment
        }

        score = CompositeScorer.calculate_composite_score(post_data)

        # Should be very low
        assert 0.0 <= score < 0.2

    def test_calculate_composite_score_medium_engagement(self):
        """Test composite score for medium engagement"""
        post_data = {
            "score": 500,  # Half of max
            "comment_count": 250,  # Half of max
            "created_utc": datetime.utcnow() - timedelta(days=45),  # Mid-age
            "text": "I struggle with this daily issue"  # Moderate pain
        }

        score = CompositeScorer.calculate_composite_score(post_data)

        # Should be medium
        assert 0.3 < score < 0.7

    def test_calculate_composite_score_missing_created_at(self):
        """Test composite score with missing timestamp"""
        post_data = {
            "score": 100,
            "comment_count": 50,
            "created_utc": None,  # Missing
            "text": "Test text"
        }

        score = CompositeScorer.calculate_composite_score(post_data)

        # Should still calculate (uses default 0.5 for recency)
        assert 0.0 <= score <= 1.0

    def test_calculate_composite_score_always_in_range(self):
        """Test that composite score is always between 0 and 1"""
        # Test extreme values
        test_cases = [
            {"score": 10000, "comment_count": 10000, "created_utc": datetime.utcnow(), "text": "hate hate hate"},
            {"score": -100, "comment_count": -100, "created_utc": datetime.utcnow() - timedelta(days=200), "text": ""},
            {"score": 0, "comment_count": 0, "created_utc": None, "text": None},
        ]

        for post_data in test_cases:
            score = CompositeScorer.calculate_composite_score(post_data)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range for {post_data}"

    def test_get_score_breakdown(self):
        """Test score breakdown returns all components"""
        post_data = {
            "score": 500,
            "comment_count": 250,
            "created_utc": datetime.utcnow() - timedelta(days=30),
            "text": "I need help with this problem"
        }

        breakdown = CompositeScorer.get_score_breakdown(post_data)

        # Verify all components present
        assert "upvotes_raw" in breakdown
        assert "upvotes_normalized" in breakdown
        assert "upvotes_contribution" in breakdown
        assert "comments_raw" in breakdown
        assert "comments_normalized" in breakdown
        assert "comments_contribution" in breakdown
        assert "recency_normalized" in breakdown
        assert "recency_contribution" in breakdown
        assert "sentiment_polarity" in breakdown
        assert "sentiment_contribution" in breakdown
        assert "composite_score" in breakdown

        # Verify contributions sum correctly (approximately)
        total_contribution = (
            breakdown["upvotes_contribution"] +
            breakdown["comments_contribution"] +
            breakdown["recency_contribution"] +
            breakdown["sentiment_contribution"]
        )

        assert abs(total_contribution - breakdown["composite_score"]) < 0.01

    def test_weight_distribution(self):
        """Test that weights sum to correct proportions"""
        # Test with all components at max (1.0 normalized)
        post_data = {
            "score": 1000,
            "comment_count": 500,
            "created_utc": datetime.utcnow(),
            "text": "terrible awful hate frustrating"  # High pain
        }

        breakdown = CompositeScorer.get_score_breakdown(post_data)

        # Weights: 0.3 (upvotes) + 0.25 (comments) + 0.25 (recency) + 0.2 (sentiment) = 1.0
        # When all normalized to 1.0:
        expected_upvotes = 0.3
        expected_comments = 0.25
        expected_recency = 0.25

        assert abs(breakdown["upvotes_contribution"] - expected_upvotes) < 0.05
        assert abs(breakdown["comments_contribution"] - expected_comments) < 0.05
        assert abs(breakdown["recency_contribution"] - expected_recency) < 0.05

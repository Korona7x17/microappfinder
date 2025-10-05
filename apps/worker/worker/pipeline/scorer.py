"""
T033: Composite scorer
Calculate relevance scores using multi-factor formula per research.md
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from textblob import TextBlob


class CompositeScorer:
    """
    Composite scoring algorithm for pain point ranking

    Formula: score = 0.3×upvotes_norm + 0.25×comments_norm + 0.25×recency_norm + 0.2×sentiment

    Components:
    - Upvotes (30%): Community validation
    - Comments (25%): Engagement depth
    - Recency (25%): Freshness
    - Sentiment (20%): Pain intensity
    """

    # Normalization constants
    MAX_UPVOTES = 1000  # Posts with 1000+ upvotes get score of 1.0
    MAX_COMMENTS = 500  # Posts with 500+ comments get score of 1.0
    MAX_AGE_DAYS = 90   # Posts older than 90 days get score of 0.0

    @classmethod
    def normalize_upvotes(cls, score: int) -> float:
        """
        Normalize upvote count to 0-1 range

        Args:
            score: Raw upvote count

        Returns:
            float: Normalized score (0-1)
        """
        if score < 0:
            return 0.0

        normalized = score / cls.MAX_UPVOTES
        return min(normalized, 1.0)

    @classmethod
    def normalize_comments(cls, count: int) -> float:
        """
        Normalize comment count to 0-1 range

        Args:
            count: Raw comment count

        Returns:
            float: Normalized score (0-1)
        """
        if count < 0:
            return 0.0

        normalized = count / cls.MAX_COMMENTS
        return min(normalized, 1.0)

    @classmethod
    def normalize_recency(cls, created_at: datetime) -> float:
        """
        Normalize post age to 0-1 range (newer = higher score)

        Args:
            created_at: Post creation timestamp

        Returns:
            float: Normalized recency score (0-1)
        """
        now = datetime.utcnow()
        age_delta = now - created_at

        # Handle future timestamps (shouldn't happen but just in case)
        if age_delta.total_seconds() < 0:
            return 1.0

        age_days = age_delta.days

        # Posts older than MAX_AGE_DAYS get 0
        if age_days >= cls.MAX_AGE_DAYS:
            return 0.0

        # Linear decay: 1.0 (today) -> 0.0 (90 days ago)
        recency = 1.0 - (age_days / cls.MAX_AGE_DAYS)
        return max(recency, 0.0)

    @classmethod
    def calculate_sentiment(cls, text: str) -> float:
        """
        Calculate sentiment polarity using TextBlob

        Args:
            text: Text to analyze (title + body)

        Returns:
            float: Sentiment polarity (-1 to 1)
                   Negative values = pain/frustration (what we want!)
        """
        if not text or len(text.strip()) == 0:
            return 0.0

        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity

            # TextBlob returns -1 to 1
            # We want negative sentiment (pain) to contribute positively to score
            # So we invert it: pain (-1) becomes high contribution, joy (+1) becomes low
            return -polarity

        except Exception as e:
            print(f"Error calculating sentiment: {e}")
            return 0.0

    @classmethod
    def calculate_composite_score(cls, post_data: Dict[str, Any]) -> float:
        """
        Calculate composite relevance score

        Args:
            post_data: Dictionary with keys:
                - score: upvote count (int)
                - comment_count: number of comments (int)
                - created_utc: post creation timestamp (datetime)
                - text: post title + body for sentiment (str)

        Returns:
            float: Composite relevance score (0-1)
        """
        # Extract data
        upvotes = post_data.get("score", 0)
        comments = post_data.get("comment_count", 0)
        created_at = post_data.get("created_utc")
        text = post_data.get("text", "")

        # Normalize components
        upvotes_norm = cls.normalize_upvotes(upvotes)
        comments_norm = cls.normalize_comments(comments)

        # Handle missing created_at
        if created_at is None:
            recency_norm = 0.5  # Default to middle value
        else:
            recency_norm = cls.normalize_recency(created_at)

        # Calculate sentiment
        sentiment_contribution = cls.calculate_sentiment(text)

        # Apply weights: 0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment
        composite_score = (
            0.30 * upvotes_norm +
            0.25 * comments_norm +
            0.25 * recency_norm +
            0.20 * sentiment_contribution
        )

        # Ensure result is in 0-1 range
        return max(0.0, min(composite_score, 1.0))

    @classmethod
    def get_score_breakdown(cls, post_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get detailed score breakdown for debugging/analysis

        Args:
            post_data: Post data dictionary

        Returns:
            dict: Breakdown of all score components
        """
        upvotes = post_data.get("score", 0)
        comments = post_data.get("comment_count", 0)
        created_at = post_data.get("created_utc")
        text = post_data.get("text", "")

        upvotes_norm = cls.normalize_upvotes(upvotes)
        comments_norm = cls.normalize_comments(comments)
        recency_norm = cls.normalize_recency(created_at) if created_at else 0.5
        sentiment = cls.calculate_sentiment(text)

        composite = cls.calculate_composite_score(post_data)

        return {
            "upvotes_raw": upvotes,
            "upvotes_normalized": round(upvotes_norm, 4),
            "upvotes_contribution": round(0.30 * upvotes_norm, 4),
            "comments_raw": comments,
            "comments_normalized": round(comments_norm, 4),
            "comments_contribution": round(0.25 * comments_norm, 4),
            "recency_normalized": round(recency_norm, 4),
            "recency_contribution": round(0.25 * recency_norm, 4),
            "sentiment_polarity": round(sentiment, 4),
            "sentiment_contribution": round(0.20 * sentiment, 4),
            "composite_score": round(composite, 4)
        }

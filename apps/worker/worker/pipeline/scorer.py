"""
T033: Composite scorer (REVISED - Phase 1 improvements)
Pain-seeking algorithm that prioritizes questions and problems over engagement
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from textblob import TextBlob
import re
import math


class CompositeScorer:
    """
    Pain-seeking scoring algorithm for opportunity discovery

    REVISED FORMULA (Phase 1):
    score = 0.15×engagement + 0.35×question_signals + 0.30×pain_intensity + 0.20×recency

    Components:
    - Engagement (15%): De-weighted from 55% - engagement ≠ pain
    - Question signals (35%): Title has "?", starts with how/why/what, help-seeking
    - Pain intensity (30%): Frequency of frustration/struggle keywords
    - Recency (20%): Freshness (unchanged)

    FILTERING:
    - Excludes success stories, announcements, updates
    - Excludes link posts (prefer text posts with context)
    """

    # Normalization constants
    MAX_UPVOTES = 1000  # Posts with 1000+ upvotes get score of 1.0
    MAX_COMMENTS = 500  # Posts with 500+ comments get score of 1.0
    MAX_AGE_DAYS = 90   # Posts older than 90 days get score of 0.0

    # Keywords for question detection
    QUESTION_STARTERS = [
        "how do i", "how can i", "how to", "how do you",
        "what is", "what are", "what's", "what should",
        "why is", "why does", "why do",
        "where can", "where do", "where should",
        "when should", "when do",
        "does anyone", "has anyone", "is there", "are there",
        "can someone", "could someone", "would anyone"
    ]

    HELP_KEYWORDS = [
        "help", "advice", "tips", "suggestions", "recommend",
        "need", "looking for", "can't figure out", "struggling to",
        "having trouble", "difficulty with", "issue with", "problem with"
    ]

    # Keywords for success story detection (EXCLUDE these)
    SUCCESS_KEYWORDS = [
        "success", "made $", "earned $", "revenue", "profit",
        "finally", "managed to", "achieved", "reached",
        "update:", "month update", "year update", "week update",
        "journey", "went from", "made it", "hit my goal",
        "launched", "just released", "proud to announce",
        "i built", "i made", "i created", "i tried", "i started"
    ]

    # Pain intensity keywords
    PAIN_KEYWORDS = [
        "frustrated", "struggling", "can't", "cannot", "unable",
        "failing", "failed", "doesn't work", "not working",
        "broken", "stuck", "confused", "lost", "overwhelmed",
        "hate", "annoying", "terrible", "awful", "waste of time",
        "give up", "giving up"
    ]

    @classmethod
    def should_filter_out(cls, post_data: Dict[str, Any]) -> bool:
        """
        Determine if post should be filtered out before scoring

        FILTERS OUT:
        - Success stories / announcements
        - Link posts (no text content)
        - Posts with success keywords in title

        Args:
            post_data: Post dictionary with title and text

        Returns:
            bool: True if should filter out, False if should keep
        """
        title = post_data.get("title", "").lower()
        text = post_data.get("text", "")

        # Filter out link posts (no self text)
        if not text or len(text.strip()) < 20:
            return True

        # Check for success keywords in title
        for keyword in cls.SUCCESS_KEYWORDS:
            if keyword in title:
                return True

        # Keep it
        return False

    @classmethod
    def calculate_question_score(cls, post_data: Dict[str, Any]) -> float:
        """
        Calculate question/help-seeking signal score

        Looks for:
        - Question mark in title
        - Question-starting phrases (how, what, why, etc.)
        - Help-seeking keywords

        Args:
            post_data: Post dictionary

        Returns:
            float: Question signal score (0-1)
        """
        title = post_data.get("title", "").lower()
        text = post_data.get("text", "").lower()

        score = 0.0

        # Question mark in title = strong signal (+0.4)
        if "?" in title:
            score += 0.4

        # Question starter phrases (+0.3 each, max 0.4)
        starter_matches = sum(1 for starter in cls.QUESTION_STARTERS if title.startswith(starter))
        score += min(starter_matches * 0.3, 0.4)

        # Help keywords in title or text (+0.1 each, max 0.3)
        help_matches = sum(1 for keyword in cls.HELP_KEYWORDS if keyword in title or keyword in text[:500])
        score += min(help_matches * 0.1, 0.3)

        return min(score, 1.0)

    @classmethod
    def calculate_pain_intensity(cls, text: str) -> float:
        """
        Calculate pain/frustration intensity from text

        Counts frequency of pain keywords and normalizes

        Args:
            text: Combined title + body text

        Returns:
            float: Pain intensity score (0-1)
        """
        if not text:
            return 0.0

        text_lower = text.lower()

        # Count pain keyword occurrences
        pain_count = sum(text_lower.count(keyword) for keyword in cls.PAIN_KEYWORDS)

        # Normalize by text length (per 1000 chars)
        text_length = len(text)
        if text_length == 0:
            return 0.0

        pain_density = (pain_count / text_length) * 1000

        # Scale: 0-5 pain keywords per 1000 chars = 0.0 to 1.0
        normalized = min(pain_density / 5.0, 1.0)

        return normalized

    @classmethod
    def normalize_engagement(cls, upvotes: int, comments: int) -> float:
        """
        Normalize engagement (upvotes + comments) using log scale

        Log scale prevents viral posts from dominating

        Args:
            upvotes: Upvote count
            comments: Comment count

        Returns:
            float: Normalized engagement (0-1)
        """
        total_engagement = max(upvotes, 0) + max(comments, 0)

        if total_engagement == 0:
            return 0.0

        # Log scale: log(1000) ≈ 6.9 → normalize to 1.0
        # This makes 1000+ engagement = 1.0, but doesn't heavily penalize low engagement
        log_engagement = math.log(total_engagement + 1)  # +1 to handle 0
        normalized = log_engagement / 7.0  # log(~1100) ≈ 7.0

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

        # Handle future timestamps
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
    def calculate_topic_relevance(cls, post_data: Dict[str, Any], topics: list) -> float:
        """
        Calculate topic relevance using keyword overlap

        Args:
            post_data: Post dictionary with title and text
            topics: List of search topic keywords

        Returns:
            float: Topic relevance score (0-1)
        """
        if not topics:
            return 1.0  # No topics = all posts relevant

        title = post_data.get("title", "").lower()
        text = post_data.get("text", "").lower()
        combined = f"{title} {text}"

        # Extract individual words from topics
        topic_words = []
        for topic in topics:
            # Split multi-word topics into individual words
            words = re.findall(r'\w+', topic.lower())
            topic_words.extend(words)

        # Remove duplicates
        topic_words = list(set(topic_words))

        if not topic_words:
            return 1.0

        # Count how many topic words appear in the post
        matches = sum(1 for word in topic_words if word in combined)

        # Normalize by number of topic words
        # Full match = 1.0, no match = 0.0
        relevance = matches / len(topic_words)

        return min(relevance, 1.0)

    @classmethod
    def calculate_composite_score(cls, post_data: Dict[str, Any], topics: list = None) -> float:
        """
        Calculate pain-seeking composite score WITH TOPIC RELEVANCE

        REVISED FORMULA:
        score = 0.10×engagement + 0.25×question + 0.20×pain + 0.15×recency + 0.30×topic_relevance

        Args:
            post_data: Dictionary with keys:
                - title: post title (str)
                - score: upvote count (int)
                - comment_count: number of comments (int)
                - created_utc: post creation timestamp (datetime)
                - text: post title + body for analysis (str)
            topics: List of search topic keywords (REQUIRED for topic relevance)

        Returns:
            float: Composite relevance score (0-1), or -1.0 if should filter out
        """
        # Pre-filter check
        if cls.should_filter_out(post_data):
            return -1.0  # Signal to caller: exclude this post

        # Extract data
        title = post_data.get("title", "")
        upvotes = post_data.get("score", 0)
        comments = post_data.get("comment_count", 0)
        created_at = post_data.get("created_utc")
        text = f"{title} {post_data.get('text', '')}"

        # Calculate components
        engagement_score = cls.normalize_engagement(upvotes, comments)
        question_score = cls.calculate_question_score(post_data)
        pain_score = cls.calculate_pain_intensity(text)
        topic_score = cls.calculate_topic_relevance(post_data, topics or [])

        # Handle missing created_at
        if created_at is None:
            recency_score = 0.5  # Default to middle value
        else:
            recency_score = cls.normalize_recency(created_at)

        # Apply NEW weights WITH TOPIC RELEVANCE
        composite_score = (
            0.10 * engagement_score +      # Reduced to 10%
            0.25 * question_score +         # Reduced to 25%
            0.20 * pain_score +             # Reduced to 20%
            0.15 * recency_score +          # Reduced to 15%
            0.30 * topic_score              # NEW: 30% topic relevance (CRITICAL)
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
        title = post_data.get("title", "")
        upvotes = post_data.get("score", 0)
        comments = post_data.get("comment_count", 0)
        created_at = post_data.get("created_utc")
        text = f"{title} {post_data.get('text', '')}"

        engagement_score = cls.normalize_engagement(upvotes, comments)
        question_score = cls.calculate_question_score(post_data)
        pain_score = cls.calculate_pain_intensity(text)
        recency_score = cls.normalize_recency(created_at) if created_at else 0.5

        composite = cls.calculate_composite_score(post_data)
        filtered = composite < 0

        return {
            "filtered_out": filtered,
            "engagement_raw": f"{upvotes} upvotes, {comments} comments",
            "engagement_normalized": round(engagement_score, 4),
            "engagement_contribution": round(0.15 * engagement_score, 4),
            "question_score": round(question_score, 4),
            "question_contribution": round(0.35 * question_score, 4),
            "pain_intensity": round(pain_score, 4),
            "pain_contribution": round(0.30 * pain_score, 4),
            "recency_normalized": round(recency_score, 4),
            "recency_contribution": round(0.20 * recency_score, 4),
            "composite_score": round(composite, 4) if not filtered else -1.0
        }

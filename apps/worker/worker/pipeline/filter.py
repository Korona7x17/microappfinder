"""
T034: NSFW/spam filter
Filter inappropriate and low-quality content per research.md
"""
from typing import Dict, Any, List
import re


class ContentFilter:
    """
    Content filtering for NSFW, spam, and low-quality posts

    Filters:
    - NSFW content (over_18 flag)
    - Spam keywords
    - Low score threshold (< 2 upvotes)
    - Deleted/removed posts
    """

    # Spam keyword blocklist
    SPAM_KEYWORDS = [
        "buy now",
        "click here",
        "crypto",
        "nft",
        "get rich quick",
        "limited time",
        "act now",
        "invest now",
        "make money fast",
        "work from home",
        "free money",
        "guaranteed",
        "no risk",
        "double your",
        "bitcoin",
        "forex",
        "mlm",
        "pyramid",
    ]

    # Minimum score threshold
    MIN_SCORE_THRESHOLD = 2

    @classmethod
    def is_nsfw(cls, post_data: Dict[str, Any]) -> bool:
        """
        Check if post is NSFW

        Args:
            post_data: Post dictionary with 'is_nsfw' key

        Returns:
            bool: True if NSFW, False otherwise
        """
        return post_data.get("is_nsfw", False)

    @classmethod
    def contains_spam_keywords(cls, text: str) -> bool:
        """
        Check if text contains spam keywords

        Args:
            text: Text to check (title + body)

        Returns:
            bool: True if spam detected, False otherwise
        """
        if not text:
            return False

        text_lower = text.lower()

        # Check each spam keyword
        for keyword in cls.SPAM_KEYWORDS:
            if keyword in text_lower:
                return True

        return False

    @classmethod
    def is_low_quality(cls, post_data: Dict[str, Any]) -> bool:
        """
        Check if post is low quality (low upvotes)

        Args:
            post_data: Post dictionary with 'score' key

        Returns:
            bool: True if low quality, False otherwise
        """
        score = post_data.get("score", 0)
        return score < cls.MIN_SCORE_THRESHOLD

    @classmethod
    def is_deleted_or_removed(cls, post_data: Dict[str, Any]) -> bool:
        """
        Check if post is deleted or removed

        Args:
            post_data: Post dictionary with 'text' and 'author' keys

        Returns:
            bool: True if deleted/removed, False otherwise
        """
        text = post_data.get("text", "")
        author = post_data.get("author")

        # Deleted posts have [deleted] text
        if text == "[deleted]":
            return True

        # Removed posts have [removed] text
        if text == "[removed]":
            return True

        # Deleted users show as None
        if author is None and (not text or text in ["[deleted]", "[removed]"]):
            return True

        return False

    @classmethod
    def is_too_short(cls, text: str, min_length: int = 20) -> bool:
        """
        Check if text is too short to be meaningful

        Args:
            text: Text to check
            min_length: Minimum character length

        Returns:
            bool: True if too short, False otherwise
        """
        if not text:
            return True

        # Remove whitespace
        cleaned_text = text.strip()

        return len(cleaned_text) < min_length

    @classmethod
    def should_filter(cls, post_data: Dict[str, Any], filter_nsfw: bool = True) -> bool:
        """
        Main filtering decision

        Args:
            post_data: Post dictionary
            filter_nsfw: Whether to filter NSFW content

        Returns:
            bool: True if post should be filtered out, False if it passes
        """
        # Filter NSFW
        if filter_nsfw and cls.is_nsfw(post_data):
            return True

        # Filter deleted/removed
        if cls.is_deleted_or_removed(post_data):
            return True

        # Filter low quality
        if cls.is_low_quality(post_data):
            return True

        # Combine title and text for spam check
        title = post_data.get("title", "")
        text = post_data.get("text", "")
        combined_text = f"{title} {text}"

        # Filter spam
        if cls.contains_spam_keywords(combined_text):
            return True

        # Filter too short
        if cls.is_too_short(combined_text, min_length=20):
            return True

        # Post passes all filters
        return False

    @classmethod
    def filter_posts(cls, posts: List[Dict[str, Any]], filter_nsfw: bool = True) -> List[Dict[str, Any]]:
        """
        Filter a list of posts

        Args:
            posts: List of post dictionaries
            filter_nsfw: Whether to filter NSFW content

        Returns:
            List[dict]: Filtered posts
        """
        filtered = []

        for post in posts:
            if not cls.should_filter(post, filter_nsfw=filter_nsfw):
                filtered.append(post)

        return filtered

    @classmethod
    def get_filter_stats(cls, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get filtering statistics

        Args:
            posts: List of post dictionaries

        Returns:
            dict: Filter statistics
        """
        stats = {
            "total": len(posts),
            "nsfw": 0,
            "spam": 0,
            "low_quality": 0,
            "deleted": 0,
            "too_short": 0,
            "passed": 0
        }

        for post in posts:
            if cls.is_nsfw(post):
                stats["nsfw"] += 1
            elif cls.is_deleted_or_removed(post):
                stats["deleted"] += 1
            elif cls.is_low_quality(post):
                stats["low_quality"] += 1
            elif cls.contains_spam_keywords(f"{post.get('title', '')} {post.get('text', '')}"):
                stats["spam"] += 1
            elif cls.is_too_short(f"{post.get('title', '')} {post.get('text', '')}"):
                stats["too_short"] += 1
            else:
                stats["passed"] += 1

        return stats

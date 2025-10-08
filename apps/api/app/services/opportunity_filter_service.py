"""
Opportunity pre-filter service
Filters candidates before LLM analysis to reduce cost
"""
from typing import List, Dict, Any
import re


class OpportunityFilterService:
    """
    Pre-filters opportunity candidates using simple heuristics

    Filters:
    1. Engagement threshold (comments > 10)
    2. Keyword matching (pain point indicators)
    3. Length threshold (meaningful content)
    """

    # Pain point indicator keywords
    PAIN_KEYWORDS = [
        # Direct problem statements
        "problem", "issue", "difficult", "struggle", "frustrated", "annoying",
        "hate", "wish", "need", "want", "looking for", "searching for",

        # Solution seeking
        "solution", "alternative", "better way", "how to", "how do i",
        "recommend", "suggestion", "tool for", "app for", "software for",

        # Willingness to pay signals
        "pay", "paid", "price", "cost", "worth", "subscription", "buy",
        "invest", "budget", "free alternative",

        # Frustration with current tools
        "doesn't work", "broken", "bug", "slow", "complicated", "confusing",
        "missing feature", "lack", "limitation", "can't do", "won't let me",

        # Market validation
        "anyone else", "does anyone", "am i the only", "everyone i know",
        "all my", "we all", "people need", "everyone needs"
    ]

    # Minimum engagement threshold
    MIN_COMMENTS = 10
    MIN_SCORE = 5
    MIN_TEXT_LENGTH = 100  # Minimum combined title + text length

    @classmethod
    def filter_candidates(
        cls,
        candidates: List[Dict[str, Any]],
        min_comments: int = None,
        min_score: int = None
    ) -> List[Dict[str, Any]]:
        """
        Filter candidates using engagement + keyword heuristics

        Args:
            candidates: List of candidate dictionaries with keys:
                - title: str
                - text: str (optional)
                - comments: int (comment_count)
                - score: int (upvotes)
                - composite_score: float
            min_comments: Override minimum comment threshold
            min_score: Override minimum score threshold

        Returns:
            Filtered list of candidates that pass all filters
        """
        min_comments = min_comments or cls.MIN_COMMENTS
        min_score = min_score or cls.MIN_SCORE

        filtered = []

        for candidate in candidates:
            # Extract fields
            title = candidate.get("title", "")
            text = candidate.get("text", "")
            comments = candidate.get("comments", candidate.get("comment_count", 0))
            score = candidate.get("score", 0)

            # Filter 1: Engagement threshold
            if comments < min_comments or score < min_score:
                continue

            # Filter 2: Minimum content length
            combined_text = f"{title} {text}"
            if len(combined_text) < cls.MIN_TEXT_LENGTH:
                continue

            # Filter 3: Keyword matching
            if not cls._has_pain_keywords(combined_text):
                continue

            filtered.append(candidate)

        return filtered

    @classmethod
    def _has_pain_keywords(cls, text: str) -> bool:
        """
        Check if text contains pain point indicator keywords

        Args:
            text: Combined title + text

        Returns:
            True if at least 2 different pain keywords found
        """
        text_lower = text.lower()

        # Count unique keyword matches
        matches = 0
        for keyword in cls.PAIN_KEYWORDS:
            if keyword in text_lower:
                matches += 1
                if matches >= 2:  # At least 2 different pain indicators
                    return True

        return False

    @classmethod
    def get_filter_stats(
        cls,
        original_count: int,
        filtered_count: int
    ) -> Dict[str, Any]:
        """
        Get statistics about filtering

        Args:
            original_count: Number of candidates before filtering
            filtered_count: Number of candidates after filtering

        Returns:
            Stats dictionary
        """
        filtered_out = original_count - filtered_count
        reduction_pct = (filtered_out / original_count * 100) if original_count > 0 else 0

        return {
            "original_count": original_count,
            "filtered_count": filtered_count,
            "filtered_out": filtered_out,
            "reduction_percentage": round(reduction_pct, 1)
        }

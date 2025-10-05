"""
T015: Cross-source deduplication service
URL-based and semantic similarity deduplication between Reddit and HackerNews
"""
from typing import List, Dict, Any, Tuple, Optional
from urllib.parse import urlparse, parse_qs
from sqlalchemy.orm import Session
from app.models.reddit_post import RedditPost
from app.models.hackernews_item import HackerNewsItem
import re
import logging

logger = logging.getLogger(__name__)


class DeduplicationService:
    """
    Cross-source deduplication service

    Features:
    - URL-based deduplication (exact match after normalization)
    - Semantic similarity using title comparison (85% threshold)
    - Merge duplicates preserving both source IDs
    - Keep higher engagement item as primary
    """

    SIMILARITY_THRESHOLD = 0.85  # 85% similarity threshold

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize deduplication service

        Args:
            db_session: Optional SQLAlchemy session
        """
        self.db = db_session

    def normalize_url(self, url: str) -> str:
        """
        Normalize URL for comparison

        Removes:
        - Query parameters (utm_*, ref, etc.)
        - Protocol differences (http vs https)
        - www prefix
        - Trailing slashes

        Args:
            url: Raw URL

        Returns:
            Normalized URL string
        """
        if not url:
            return ""

        # Parse URL
        parsed = urlparse(url)

        # Normalize domain (remove www, lowercase)
        domain = parsed.netloc.lower().replace("www.", "")

        # Keep only path (ignore query params)
        path = parsed.path.rstrip("/")

        # Return normalized URL
        return f"{domain}{path}"

    def is_duplicate_by_url(
        self,
        item1: Dict[str, Any],
        item2: Dict[str, Any]
    ) -> bool:
        """
        Check if two items are duplicates based on URL

        Args:
            item1: First item (Reddit or HN)
            item2: Second item (Reddit or HN)

        Returns:
            True if URLs match after normalization
        """
        url1 = item1.get("url", "")
        url2 = item2.get("url", "")

        if not url1 or not url2:
            return False

        normalized1 = self.normalize_url(url1)
        normalized2 = self.normalize_url(url2)

        return normalized1 == normalized2 and normalized1 != ""

    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles

        Uses simple token-based Jaccard similarity
        Removes common prefixes: "Ask HN:", "Ask Reddit:", etc.

        Args:
            title1: First title
            title2: Second title

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Remove common prefixes
        prefixes = [
            r"^ask hn:\s*",
            r"^show hn:\s*",
            r"^ask reddit:\s*",
            r"^\[ask\]\s*",
            r"^\[show\]\s*"
        ]

        clean1 = title1.lower()
        clean2 = title2.lower()

        for prefix in prefixes:
            clean1 = re.sub(prefix, "", clean1, flags=re.IGNORECASE)
            clean2 = re.sub(prefix, "", clean2, flags=re.IGNORECASE)

        # Tokenize
        tokens1 = set(clean1.split())
        tokens2 = set(clean2.split())

        # Calculate Jaccard similarity
        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        return len(intersection) / len(union)

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between texts

        For MVP: Uses title similarity
        Future: Could use embeddings (sentence-transformers)

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        return self.calculate_title_similarity(text1, text2)

    def deduplicate_cross_source(
        self,
        reddit_posts: List[RedditPost],
        hn_items: List[HackerNewsItem]
    ) -> Dict[str, Any]:
        """
        Deduplicate between Reddit and HackerNews items

        Strategy:
        1. URL-based exact match
        2. Title similarity (>= 85%)
        3. Merge duplicates, keep higher engagement

        Args:
            reddit_posts: List of RedditPost objects
            hn_items: List of HackerNewsItem objects

        Returns:
            Dictionary with:
            - unique_items: List of deduplicated items
            - duplicates: List of duplicate pairs
        """
        unique_items = []
        duplicates = []
        processed_hn_ids = set()

        logger.info(f"Deduplicating {len(reddit_posts)} Reddit + {len(hn_items)} HN items")

        # Convert to dictionaries for easier comparison
        reddit_dicts = [self._reddit_to_dict(post) for post in reddit_posts]
        hn_dicts = [self._hn_to_dict(item) for item in hn_items]

        # Check each Reddit post against HN items
        for reddit_dict in reddit_dicts:
            found_duplicate = False

            for hn_dict in hn_dicts:
                if hn_dict["id"] in processed_hn_ids:
                    continue

                # Check URL-based duplicate
                if self.is_duplicate_by_url(reddit_dict, hn_dict):
                    found_duplicate = True
                    merged = self._merge_items(reddit_dict, hn_dict)
                    unique_items.append(merged)
                    duplicates.append({
                        "reddit_id": reddit_dict["id"],
                        "hn_id": hn_dict["id"],
                        "method": "url"
                    })
                    processed_hn_ids.add(hn_dict["id"])
                    break

                # Check semantic similarity
                similarity = self.calculate_title_similarity(
                    reddit_dict["title"],
                    hn_dict["title"]
                )

                if similarity >= self.SIMILARITY_THRESHOLD:
                    found_duplicate = True
                    merged = self._merge_items(reddit_dict, hn_dict)
                    unique_items.append(merged)
                    duplicates.append({
                        "reddit_id": reddit_dict["id"],
                        "hn_id": hn_dict["id"],
                        "method": "semantic",
                        "similarity": similarity
                    })
                    processed_hn_ids.add(hn_dict["id"])
                    break

            if not found_duplicate:
                unique_items.append(reddit_dict)

        # Add remaining HN items (no duplicates found)
        for hn_dict in hn_dicts:
            if hn_dict["id"] not in processed_hn_ids:
                unique_items.append(hn_dict)

        logger.info(f"Deduplication complete: {len(unique_items)} unique, {len(duplicates)} duplicates")

        return {
            "unique_items": unique_items,
            "duplicates": duplicates
        }

    def _reddit_to_dict(self, post: RedditPost) -> Dict[str, Any]:
        """Convert RedditPost to dictionary"""
        return {
            "id": post.reddit_id,
            "source": "reddit",
            "title": post.title,
            "text": post.selftext,
            "url": post.url,
            "score": post.score,
            "comment_count": post.num_comments,
            "created_at": post.created_utc,
            "source_ids": [post.reddit_id]
        }

    def _hn_to_dict(self, item: HackerNewsItem) -> Dict[str, Any]:
        """Convert HackerNewsItem to dictionary"""
        return {
            "id": item.hn_id,
            "source": "hackernews",
            "title": item.title,
            "text": item.text,
            "url": item.url,
            "score": item.points,
            "comment_count": item.comment_count,
            "created_at": item.created_utc,
            "source_ids": [item.hn_id]
        }

    def _merge_items(
        self,
        reddit_dict: Dict[str, Any],
        hn_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge duplicate items, keeping higher engagement

        Args:
            reddit_dict: Reddit item dictionary
            hn_dict: HN item dictionary

        Returns:
            Merged item dictionary
        """
        # Calculate engagement scores (simple sum for now)
        reddit_engagement = reddit_dict["score"] + reddit_dict["comment_count"]
        hn_engagement = hn_dict["score"] + hn_dict["comment_count"]

        # Keep item with higher engagement
        if hn_engagement > reddit_engagement:
            primary = hn_dict.copy()
            primary["source_ids"] = [reddit_dict["id"], hn_dict["id"]]
            return primary
        else:
            primary = reddit_dict.copy()
            primary["source_ids"] = [reddit_dict["id"], hn_dict["id"]]
            return primary

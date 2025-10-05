"""
T014: HackerNews fetch service
Algolia HN API client with 48h caching and cleanup
"""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.hackernews_item import HackerNewsItem
from app.core.circuit_breaker import get_circuit_breaker
import logging

logger = logging.getLogger(__name__)

# Algolia HackerNews API
HN_ALGOLIA_API = "https://hn.algolia.com/api/v1"
HN_SEARCH_ENDPOINT = f"{HN_ALGOLIA_API}/search"
HN_ITEM_ENDPOINT = f"{HN_ALGOLIA_API}/items"


class HackerNewsService:
    """
    HackerNews service using Algolia API

    Features:
    - Algolia HN API integration (no rate limits)
    - 48h cache pattern (mirrors RedditPost)
    - Ask HN focus for pain points
    - Minimum engagement thresholds
    - Automatic cache cleanup
    """

    def __init__(self, db_session: Session):
        """
        Initialize HackerNews service

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.client = httpx.Client(timeout=30.0)
        # Circuit breaker for Algolia API (Feature 002: T020)
        self.circuit_breaker = get_circuit_breaker(
            name="hackernews_algolia",
            failure_threshold=3,  # Open after 3 failures
            timeout=120,          # Wait 2 minutes before retry
            success_threshold=2   # Need 2 successes to close
        )

    def fetch_stories(
        self,
        query: str,
        tags: Optional[str] = "ask_hn",
        min_points: int = 10,
        days_back: int = 30,
        page: int = 0,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch HN stories from Algolia API

        Args:
            query: Search query string
            tags: Filter by tags (ask_hn, show_hn, story)
            min_points: Minimum points threshold
            days_back: Look back N days
            page: Page number (0-indexed)
            per_page: Results per page

        Returns:
            List of story dictionaries
        """
        logger.info(f"Fetching HN stories: query='{query}', tags='{tags}'")

        # Calculate timestamp for time filter
        cutoff_timestamp = int((datetime.utcnow() - timedelta(days=days_back)).timestamp())

        params = {
            "query": query,
            "tags": tags,
            "numericFilters": f"created_at_i>{cutoff_timestamp},points>={min_points}",
            "page": page,
            "hitsPerPage": per_page
        }

        def _fetch_from_api():
            """Internal function to fetch from API (wrapped by circuit breaker)"""
            response = self.client.get(HN_SEARCH_ENDPOINT, params=params)
            response.raise_for_status()
            return response.json()

        try:
            # Execute through circuit breaker (Feature 002: T020)
            data = self.circuit_breaker.call(_fetch_from_api)
            hits = data.get("hits", [])

            logger.info(f"Fetched {len(hits)} HN stories")

            return [self._normalize_hit(hit) for hit in hits]

        except httpx.HTTPError as e:
            logger.error(f"Algolia API error: {e}")
            raise Exception(f"Failed to fetch HN stories: {e}")
        except Exception as e:
            if "Circuit breaker" in str(e):
                logger.warning(f"HN API unavailable (circuit open): {e}")
                return []  # Return empty results when circuit is open
            raise

    def _normalize_hit(self, hit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Algolia hit to standard format

        Args:
            hit: Algolia API hit object

        Returns:
            Normalized story dictionary
        """
        return {
            "hn_id": hit.get("objectID"),
            "hn_type": hit.get("_tags", ["story"])[0] if hit.get("_tags") else "story",
            "author": hit.get("author"),
            "title": hit.get("title", ""),
            "text": hit.get("story_text") or hit.get("comment_text"),
            "url": hit.get("url"),
            "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "points": hit.get("points", 0),
            "comment_count": hit.get("num_comments", 0),
            "created_at_i": hit.get("created_at_i")
        }

    def fetch_and_cache_stories(
        self,
        query: str,
        tags: Optional[str] = "ask_hn",
        min_points: int = 10,
        days_back: int = 30
    ) -> List[HackerNewsItem]:
        """
        Fetch stories and store in 48h cache

        Args:
            query: Search query
            tags: HN tags filter
            min_points: Minimum points
            days_back: Time range in days

        Returns:
            List of cached HackerNewsItem objects
        """
        stories = self.fetch_stories(
            query=query,
            tags=tags,
            min_points=min_points,
            days_back=days_back
        )

        cached_items = []

        for story in stories:
            # Check if already cached and not expired
            existing = self.get_cached_item(story["hn_id"])

            if existing and not existing.is_expired:
                logger.debug(f"Using cached HN item: {story['hn_id']}")
                cached_items.append(existing)
                continue

            # Create new cache entry
            created_utc = datetime.utcfromtimestamp(story["created_at_i"])
            expires_at = datetime.utcnow() + timedelta(hours=48)

            item = HackerNewsItem(
                hn_id=story["hn_id"],
                hn_type=story["hn_type"],
                author=story["author"],
                title=story["title"],
                text=story["text"],
                url=story["url"],
                hn_url=story["hn_url"],
                points=story["points"],
                comment_count=story["comment_count"],
                created_utc=created_utc,
                expires_at=expires_at
            )

            # Handle duplicates with merge
            self.db.merge(item)
            cached_items.append(item)

        self.db.commit()
        logger.info(f"Cached {len(cached_items)} HN items")

        return cached_items

    def get_cached_item(self, hn_id: str) -> Optional[HackerNewsItem]:
        """
        Get cached HN item by ID (returns None if expired)

        Args:
            hn_id: HackerNews item ID

        Returns:
            HackerNewsItem or None
        """
        item = self.db.query(HackerNewsItem).filter_by(hn_id=hn_id).first()

        if item and item.is_expired:
            return None

        return item

    def fetch_comments(self, hn_id: str) -> List[Dict[str, Any]]:
        """
        Fetch comments for a HN story

        Args:
            hn_id: HackerNews item ID

        Returns:
            List of comment dictionaries
        """
        try:
            response = self.client.get(f"{HN_ITEM_ENDPOINT}/{hn_id}")
            response.raise_for_status()

            data = response.json()
            children = data.get("children", [])

            comments = []
            for child in children:
                if child.get("text"):
                    comments.append({
                        "id": child.get("id"),
                        "author": child.get("author"),
                        "text": child.get("text"),
                        "created_at_i": child.get("created_at_i")
                    })

            return comments

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch comments for {hn_id}: {e}")
            return []

    def cleanup_expired_cache(self) -> int:
        """
        Delete expired cache entries (48h TTL)

        Returns:
            Number of items deleted
        """
        now = datetime.utcnow()

        # Find expired items
        expired_items = self.db.query(HackerNewsItem).filter(
            HackerNewsItem.expires_at < now
        ).all()

        count = len(expired_items)

        # Delete expired items
        for item in expired_items:
            self.db.delete(item)

        self.db.commit()

        logger.info(f"Cleaned up {count} expired HN cache items")

        return count

    def __del__(self):
        """Close HTTP client on cleanup"""
        if hasattr(self, 'client'):
            self.client.close()

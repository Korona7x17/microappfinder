"""
T016: Unified search service
Multi-source aggregation with composite scoring
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.reddit_post import RedditPost
from app.models.hackernews_item import HackerNewsItem
from app.services.deduplication_service import DeduplicationService
import logging

logger = logging.getLogger(__name__)


class UnifiedSearchService:
    """
    Unified search service for multi-source aggregation

    Features:
    - Aggregates Reddit + HackerNews results
    - Composite scoring: 0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment
    - Cross-platform ranking
    - Pagination support
    - Source filtering
    """

    # Composite score weights
    WEIGHT_UPVOTES = 0.30
    WEIGHT_COMMENTS = 0.25
    WEIGHT_RECENCY = 0.25
    WEIGHT_SENTIMENT = 0.20

    def __init__(self, db_session: Session):
        """
        Initialize unified search service

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.dedup_service = DeduplicationService(db_session)

    def aggregate_sources(
        self,
        reddit_posts: List[RedditPost],
        hn_items: List[HackerNewsItem]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate results from multiple sources

        Args:
            reddit_posts: List of Reddit posts
            hn_items: List of HN items

        Returns:
            List of unified result dictionaries
        """
        results = []

        # Add Reddit posts
        for post in reddit_posts:
            results.append({
                "id": post.reddit_id,
                "source": "reddit",
                "title": post.title,
                "text": post.text,
                "url": post.url,
                "created_at": post.created_utc,
                "upvotes": post.score,
                "comments": post.comment_count,
                "metadata": {
                    "subreddit": post.subreddit,
                    "author": post.author
                }
            })

        # Add HN items
        for item in hn_items:
            results.append({
                "id": item.hn_id,
                "source": "hackernews",
                "title": item.title,
                "text": item.text,
                "url": item.url,
                "created_at": item.created_utc,
                "upvotes": item.points,
                "comments": item.comment_count,
                "metadata": {
                    "hn_type": item.hn_type,
                    "author": item.author
                }
            })

        return results

    def calculate_composite_score(
        self,
        upvotes: int,
        comments: int,
        created_at: datetime,
        sentiment: float = 0.0
    ) -> float:
        """
        Calculate composite score for ranking

        Formula: 0.3×upvotes_norm + 0.25×comments_norm + 0.25×recency + 0.2×sentiment

        Args:
            upvotes: Upvote/points count
            comments: Comment count
            created_at: Creation timestamp
            sentiment: Sentiment score (-1 to 1)

        Returns:
            Composite score (0.0 to 1.0)
        """
        # Normalize upvotes (log scale for better distribution)
        import math
        upvotes_norm = math.log(upvotes + 1) / math.log(1000)  # Normalize to ~1000 max
        upvotes_norm = min(upvotes_norm, 1.0)

        # Normalize comments
        comments_norm = math.log(comments + 1) / math.log(500)  # Normalize to ~500 max
        comments_norm = min(comments_norm, 1.0)

        # Calculate recency score (exponential decay over 30 days)
        age_days = (datetime.utcnow() - created_at).total_seconds() / 86400
        recency = math.exp(-age_days / 30.0)  # Half-life ~30 days

        # Normalize sentiment from [-1, 1] to [0, 1]
        sentiment_norm = (sentiment + 1) / 2.0

        # Calculate weighted composite score
        score = (
            self.WEIGHT_UPVOTES * upvotes_norm +
            self.WEIGHT_COMMENTS * comments_norm +
            self.WEIGHT_RECENCY * recency +
            self.WEIGHT_SENTIMENT * sentiment_norm
        )

        return min(score, 1.0)

    def aggregate_and_rank(
        self,
        reddit_posts: List[RedditPost],
        hn_items: List[HackerNewsItem],
        time_range: Optional[str] = None,
        source_filter: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Aggregate, score, and rank results from multiple sources

        Args:
            reddit_posts: List of Reddit posts
            hn_items: List of HN items
            time_range: Optional time filter (7days, 30days, etc.)
            source_filter: Optional source filter (reddit, hackernews)
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            Ranked and paginated results
        """
        # Aggregate sources
        results = self.aggregate_sources(reddit_posts, hn_items)

        # Apply time range filter
        if time_range:
            cutoff = self._get_time_cutoff(time_range)
            results = [r for r in results if r["created_at"] >= cutoff]

        # Apply source filter
        if source_filter:
            results = [r for r in results if r["source"] == source_filter]

        # Calculate composite scores
        for result in results:
            result["composite_score"] = self.calculate_composite_score(
                upvotes=result["upvotes"],
                comments=result["comments"],
                created_at=result["created_at"],
                sentiment=0.0  # TODO: Implement sentiment analysis
            )

        # Sort by composite score (descending)
        results.sort(key=lambda x: x["composite_score"], reverse=True)

        # Paginate
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = results[start_idx:end_idx]

        logger.info(
            f"Unified search: {len(results)} total, returning page {page} "
            f"({len(paginated_results)} items)"
        )

        return paginated_results

    def normalize_engagement_score(
        self,
        score: int,
        max_score: int,
        platform: str
    ) -> float:
        """
        Normalize engagement scores across platforms

        Args:
            score: Raw engagement score
            max_score: Maximum score for normalization
            platform: Source platform

        Returns:
            Normalized score (0.0 to 1.0)
        """
        if max_score == 0:
            return 0.0

        normalized = score / max_score

        # Platform-specific adjustments (if needed)
        # HN typically has lower scores than Reddit
        if platform == "hackernews":
            normalized = min(normalized * 1.2, 1.0)  # Slight boost

        return min(normalized, 1.0)

    def _get_time_cutoff(self, time_range: str) -> datetime:
        """
        Get cutoff datetime for time range filter

        Args:
            time_range: Time range string (24h, 7days, 30days, etc.)

        Returns:
            Cutoff datetime
        """
        now = datetime.utcnow()

        time_deltas = {
            "24h": timedelta(hours=24),
            "7days": timedelta(days=7),
            "30days": timedelta(days=30),
            "90days": timedelta(days=90),
            "1year": timedelta(days=365),
        }

        delta = time_deltas.get(time_range, timedelta(days=30))
        return now - delta

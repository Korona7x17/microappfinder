"""
T026: Deletion sync service
Daily job to check for deleted Reddit posts and update database (Reddit ToS compliance)
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Dict
from datetime import datetime, timedelta
import redis
import os

from app.models.reddit_post import RedditPost
from app.models.pain_point import PainPoint
from .reddit_api import RedditAPIClient


class DeletionSyncService:
    """
    Deletion sync service for Reddit ToS compliance

    Features:
    - Daily check for deleted Reddit posts
    - Purge from Redis cache
    - Update PainPoint.source_deleted flag
    - Automatic TTL cleanup for expired posts (48h)

    ⚠️ CRITICAL: Required for Reddit API ToS compliance
    """

    def __init__(self, db: Session, redis_client: redis.Redis = None):
        """
        Initialize deletion sync service

        Args:
            db: SQLAlchemy database session
            redis_client: Redis client for cache operations
        """
        self.db = db
        self.reddit_api = RedditAPIClient()

        # Initialize Redis client
        if redis_client is None:
            self.redis = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                decode_responses=True
            )
        else:
            self.redis = redis_client

    def cleanup_expired_posts(self) -> int:
        """
        Remove expired posts from database (48h TTL)

        Returns:
            int: Number of posts deleted
        """
        now = datetime.utcnow()

        # Find expired posts
        expired_posts = self.db.execute(
            select(RedditPost).where(RedditPost.expires_at <= now)
        ).scalars().all()

        count = len(expired_posts)

        # Delete from database
        for post in expired_posts:
            # Remove from Redis cache
            redis_key = f"reddit:post:{post.reddit_id}"
            self.redis.delete(redis_key)

            # Delete from database
            self.db.delete(post)

        self.db.commit()

        print(f"Cleaned up {count} expired Reddit posts (48h TTL)")
        return count

    def sync_deleted_posts(self, batch_size: int = 100) -> Dict[str, int]:
        """
        Check Reddit API for deleted posts and update database

        Args:
            batch_size: Number of posts to check per batch

        Returns:
            dict: {"checked": int, "deleted": int, "pain_points_updated": int}
        """
        stats = {
            "checked": 0,
            "deleted": 0,
            "pain_points_updated": 0
        }

        # Get all non-expired posts
        now = datetime.utcnow()
        posts = self.db.execute(
            select(RedditPost).where(RedditPost.expires_at > now)
        ).scalars().all()

        # Process in batches
        reddit_ids = [post.reddit_id for post in posts]

        for i in range(0, len(reddit_ids), batch_size):
            batch = reddit_ids[i:i + batch_size]

            # Batch check deletion status
            deletion_status = self.reddit_api.batch_check_deleted(batch)

            for reddit_id, is_deleted in deletion_status.items():
                stats["checked"] += 1

                if is_deleted:
                    # Post was deleted on Reddit
                    stats["deleted"] += 1

                    # Remove from Redis cache
                    redis_key = f"reddit:post:{reddit_id}"
                    self.redis.delete(redis_key)

                    # Find post in database
                    post = self.db.execute(
                        select(RedditPost).where(RedditPost.reddit_id == reddit_id)
                    ).scalar_one_or_none()

                    if post:
                        # Update pain points that reference this post
                        pain_points = self.db.execute(
                            select(PainPoint).where(
                                PainPoint.source_reddit_post_ids.contains([reddit_id])
                            )
                        ).scalars().all()

                        for pain_point in pain_points:
                            pain_point.source_deleted = True
                            stats["pain_points_updated"] += 1

                        # Delete post from database
                        self.db.delete(post)

        self.db.commit()

        print(f"Deletion sync: checked={stats['checked']}, deleted={stats['deleted']}, pain_points_updated={stats['pain_points_updated']}")
        return stats

    def run_daily_sync(self) -> Dict[str, int]:
        """
        Run complete daily synchronization

        Returns:
            dict: Combined stats from cleanup and sync
        """
        print(f"Starting daily Reddit deletion sync at {datetime.utcnow()}")

        # Step 1: Clean up expired posts (48h TTL)
        expired_count = self.cleanup_expired_posts()

        # Step 2: Sync deleted posts
        sync_stats = self.sync_deleted_posts()

        # Combine stats
        stats = {
            "expired_cleaned": expired_count,
            **sync_stats
        }

        print(f"Daily sync complete: {stats}")
        return stats

    def get_redis_cache_stats(self) -> Dict[str, int]:
        """
        Get Redis cache statistics

        Returns:
            dict: {"total_keys": int, "memory_usage": int}
        """
        # Count reddit post keys
        pattern = "reddit:post:*"
        keys = self.redis.keys(pattern)

        return {
            "total_keys": len(keys),
            "memory_usage": self.redis.info("memory")["used_memory"]
        }

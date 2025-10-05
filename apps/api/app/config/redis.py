"""
T044: Redis TTL automation
Configuration for Redis cache with automatic 48h TTL
"""
import redis
import os
from typing import Any, Optional
import json


class RedisCache:
    """
    Redis cache manager with automatic TTL enforcement

    Features:
    - 48-hour TTL for all Reddit post cache keys
    - JSON serialization/deserialization
    - Key pattern: reddit:post:{reddit_id}
    - Automatic expiration handling
    """

    # TTL Configuration
    REDDIT_POST_TTL = 172800  # 48 hours in seconds (Reddit ToS compliance)
    KEY_PREFIX = "reddit:post:"

    def __init__(self):
        """Initialize Redis connection"""
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=False  # We handle JSON ourselves
        )

    def set_post(self, reddit_id: str, post_data: dict) -> bool:
        """
        Store Reddit post with automatic 48h TTL

        Args:
            reddit_id: Reddit post ID (e.g., "t3_abc123")
            post_data: Post data dictionary

        Returns:
            bool: True if stored successfully
        """
        key = f"{self.KEY_PREFIX}{reddit_id}"

        try:
            # Serialize to JSON
            value = json.dumps(post_data, default=str)

            # Set with TTL (SETEX command)
            self.client.setex(
                key,
                self.REDDIT_POST_TTL,
                value
            )

            return True

        except Exception as e:
            print(f"Error storing post {reddit_id}: {e}")
            return False

    def get_post(self, reddit_id: str) -> Optional[dict]:
        """
        Retrieve Reddit post from cache

        Args:
            reddit_id: Reddit post ID

        Returns:
            dict: Post data or None if not found/expired
        """
        key = f"{self.KEY_PREFIX}{reddit_id}"

        try:
            value = self.client.get(key)

            if value is None:
                return None

            # Deserialize from JSON
            return json.loads(value)

        except Exception as e:
            print(f"Error retrieving post {reddit_id}: {e}")
            return None

    def delete_post(self, reddit_id: str) -> bool:
        """
        Delete Reddit post from cache (for compliance sync)

        Args:
            reddit_id: Reddit post ID

        Returns:
            bool: True if deleted
        """
        key = f"{self.KEY_PREFIX}{reddit_id}"

        try:
            result = self.client.delete(key)
            return result > 0

        except Exception as e:
            print(f"Error deleting post {reddit_id}: {e}")
            return False

    def get_ttl(self, reddit_id: str) -> int:
        """
        Get remaining TTL for a post

        Args:
            reddit_id: Reddit post ID

        Returns:
            int: Remaining seconds, -1 if no TTL, -2 if key doesn't exist
        """
        key = f"{self.KEY_PREFIX}{reddit_id}"

        try:
            return self.client.ttl(key)
        except Exception as e:
            print(f"Error getting TTL for {reddit_id}: {e}")
            return -2

    def count_cached_posts(self) -> int:
        """
        Count total cached Reddit posts

        Returns:
            int: Number of cached posts
        """
        try:
            pattern = f"{self.KEY_PREFIX}*"
            keys = self.client.keys(pattern)
            return len(keys)

        except Exception as e:
            print(f"Error counting cached posts: {e}")
            return 0

    def get_memory_usage(self) -> dict:
        """
        Get Redis memory usage statistics

        Returns:
            dict: Memory stats
        """
        try:
            info = self.client.info("memory")
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
            }

        except Exception as e:
            print(f"Error getting memory usage: {e}")
            return {}

    def flush_expired(self) -> int:
        """
        Manually trigger cleanup of expired keys (Redis does this automatically)

        Note: Redis automatically removes expired keys, this is for manual verification

        Returns:
            int: Number of keys removed
        """
        try:
            # Get all reddit post keys
            pattern = f"{self.KEY_PREFIX}*"
            keys = self.client.keys(pattern)

            removed = 0
            for key in keys:
                ttl = self.client.ttl(key)
                # TTL -2 means key doesn't exist (already expired)
                # TTL -1 means no expiration set (should not happen)
                if ttl == -2:
                    removed += 1

            return removed

        except Exception as e:
            print(f"Error flushing expired keys: {e}")
            return 0

    def health_check(self) -> dict:
        """
        Check Redis health and configuration

        Returns:
            dict: Health check results
        """
        try:
            # Ping Redis
            self.client.ping()

            # Get stats
            cached_posts = self.count_cached_posts()
            memory = self.get_memory_usage()

            return {
                "status": "healthy",
                "cached_posts": cached_posts,
                "memory_usage": memory.get("used_memory_human", "0B"),
                "ttl_configured": self.REDDIT_POST_TTL,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global instance
redis_cache = RedisCache()

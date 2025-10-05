"""
T035: Scheduled deletion sync job
Daily job to sync deleted Reddit posts (Reddit ToS compliance)
"""
from datetime import datetime
import redis
import os

# Database imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../api'))

from app.database import SessionLocal
from app.services.deletion_sync import DeletionSyncService


def run_deletion_sync():
    """
    RQ Scheduler job: Daily deletion sync

    Schedule: Daily at 2:00 AM UTC

    Steps:
        1. Clean up expired posts (48h TTL)
        2. Check Reddit API for deleted posts
        3. Remove from Redis cache
        4. Update PainPoint.source_deleted flag
        5. Delete from PostgreSQL

    Returns:
        dict: Sync statistics
    """
    print(f"=== Starting Reddit Deletion Sync at {datetime.utcnow()} ===")

    db = SessionLocal()
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )

    try:
        # Initialize deletion sync service
        sync_service = DeletionSyncService(db=db, redis_client=redis_client)

        # Run daily sync
        stats = sync_service.run_daily_sync()

        # Get Redis cache stats
        cache_stats = sync_service.get_redis_cache_stats()

        print(f"=== Deletion Sync Complete ===")
        print(f"Expired cleaned: {stats['expired_cleaned']}")
        print(f"Posts checked: {stats['checked']}")
        print(f"Deleted posts found: {stats['deleted']}")
        print(f"Pain points updated: {stats['pain_points_updated']}")
        print(f"Redis cache keys: {cache_stats['total_keys']}")
        print(f"Redis memory usage: {cache_stats['memory_usage']} bytes")

        return {
            **stats,
            "cache_keys": cache_stats["total_keys"],
            "cache_memory": cache_stats["memory_usage"],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"Error during deletion sync: {str(e)}")
        raise

    finally:
        db.close()
        redis_client.close()


def schedule_deletion_sync(scheduler):
    """
    Schedule the deletion sync job

    Args:
        scheduler: RQ Scheduler instance

    Usage:
        from rq_scheduler import Scheduler
        from worker.jobs.deletion_sync import schedule_deletion_sync

        scheduler = Scheduler(connection=redis_conn)
        schedule_deletion_sync(scheduler)
    """
    # Schedule daily at 2:00 AM UTC
    scheduler.cron(
        "0 2 * * *",  # Cron expression: every day at 2:00 AM
        func=run_deletion_sync,
        queue_name="default",
        timeout=3600,  # 1 hour timeout
        id="daily_deletion_sync"
    )

    print("Scheduled daily deletion sync job at 2:00 AM UTC")

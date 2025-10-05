"""
T017: Scheduled HackerNews cache cleanup job
Daily job to clean up expired HN items (48h TTL)
"""
from datetime import datetime
import os

# Database imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../api'))

from app.database import SessionLocal
from app.services.hackernews_service import HackerNewsService


def run_hn_cache_cleanup():
    """
    RQ Scheduler job: Daily HN cache cleanup

    Schedule: Daily at 3:00 AM UTC (after Reddit sync at 2:00 AM)

    Steps:
        1. Query all HackerNewsItem records
        2. Delete items where expires_at < now (48h TTL)
        3. Return cleanup statistics

    Returns:
        dict: Cleanup statistics
    """
    print(f"=== Starting HackerNews Cache Cleanup at {datetime.utcnow()} ===")

    db = SessionLocal()

    try:
        # Initialize HN service
        hn_service = HackerNewsService(db_session=db)

        # Run cleanup
        deleted_count = hn_service.cleanup_expired_cache()

        print(f"=== HN Cache Cleanup Complete ===")
        print(f"Expired items deleted: {deleted_count}")

        return {
            "deleted_count": deleted_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"Error during HN cache cleanup: {str(e)}")
        raise

    finally:
        db.close()


def schedule_hn_cache_cleanup(scheduler):
    """
    Schedule the HN cache cleanup job

    Args:
        scheduler: RQ Scheduler instance

    Usage:
        from rq_scheduler import Scheduler
        from worker.jobs.hackernews_cleanup import schedule_hn_cache_cleanup

        scheduler = Scheduler(connection=redis_conn)
        schedule_hn_cache_cleanup(scheduler)
    """
    # Schedule daily at 3:00 AM UTC (after Reddit deletion sync)
    scheduler.cron(
        "0 3 * * *",  # Cron expression: every day at 3:00 AM
        func=run_hn_cache_cleanup,
        queue_name="default",
        timeout=1800,  # 30 minute timeout
        id="daily_hn_cache_cleanup"
    )

    print("Scheduled daily HN cache cleanup job at 3:00 AM UTC")

"""
RQ Worker entry point
"""
import os
import redis
from rq import Worker, Queue, Connection
from rq_scheduler import Scheduler

# Import jobs to register them
from worker.jobs.deletion_sync import schedule_deletion_sync
from worker.jobs.hackernews_cleanup import schedule_hn_cache_cleanup

# Import tasks to register them with RQ
from worker.tasks.reddit_search import process_search
from worker.tasks.hackernews_search import fetch_hn_for_search
from worker.tasks.unified_search import aggregate_and_extract_unified


def start_worker():
    """Start RQ worker"""
    # Redis connection
    redis_conn = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0))
    )

    # Create queues
    queues = [
        Queue("default", connection=redis_conn),
        Queue("high", connection=redis_conn),
        Queue("low", connection=redis_conn)
    ]

    # Start worker
    with Connection(redis_conn):
        worker = Worker(queues)
        worker.work()


def start_scheduler():
    """Start RQ Scheduler for scheduled jobs"""
    # Redis connection
    redis_conn = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0))
    )

    # Create scheduler
    scheduler = Scheduler(connection=redis_conn)

    # Schedule jobs
    schedule_deletion_sync(scheduler)
    schedule_hn_cache_cleanup(scheduler)

    print("RQ Scheduler started. Scheduled jobs:")
    print("- Daily deletion sync: 2:00 AM UTC")
    print("- Daily HackerNews cleanup: 3:00 AM UTC")

    # Run scheduler
    scheduler.run()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "scheduler":
        start_scheduler()
    else:
        start_worker()

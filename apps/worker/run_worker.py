#!/usr/bin/env python
"""
RQ Worker runner with proper imports
This script ensures all modules are importable before starting the worker
"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add both API and worker to Python path
sys.path.insert(0, '/app/worker')  # For Docker
sys.path.insert(0, '/app')  # For API models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # For local

# Import Redis and RQ
from redis import Redis
from rq import Worker, Queue, Connection

# Set environment variables if not set
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/microappfinder')
os.environ.setdefault('REDIS_URL', 'redis://redis:6379/0')

# Now import the task modules to register them
try:
    from worker.tasks.reddit_search import process_search
    from worker.tasks.hackernews_search import fetch_hn_for_search
    from worker.tasks.unified_search import aggregate_and_extract_unified
    logger.info("Successfully imported all task modules")
except ImportError as e:
    logger.error(f"Failed to import task modules: {e}")
    # Try alternative import path
    try:
        sys.path.insert(0, '/app/worker/worker')
        from tasks.reddit_search import process_search
        from tasks.hackernews_search import fetch_hn_for_search
        from tasks.unified_search import aggregate_and_extract_unified
        logger.info("Successfully imported task modules using alternative path")
    except ImportError as e2:
        logger.error(f"Failed with alternative path too: {e2}")
        raise

if __name__ == '__main__':
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    logger.info(f"Connecting to Redis at: {redis_url}")

    conn = Redis.from_url(redis_url)

    # Test Redis connection
    try:
        conn.ping()
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

    with Connection(conn):
        worker = Worker(['default'], log_job_description=True)
        logger.info("Starting RQ worker...")
        worker.work()
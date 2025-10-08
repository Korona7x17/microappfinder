#!/usr/bin/env python
"""Start RQ worker with proper imports"""
import sys
import os

# Add paths for imports
sys.path.insert(0, '/app/worker')
sys.path.insert(0, '/app')

# Now start the RQ worker
from rq import Worker, Queue, Connection
import redis

# Import the tasks to register them
from worker.tasks.reddit_search import process_search
from worker.tasks.hackernews_search import fetch_hn_for_search
from worker.tasks.unified_search import aggregate_and_extract_unified

if __name__ == '__main__':
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    conn = redis.from_url(redis_url)

    with Connection(conn):
        worker = Worker(['default'])
        worker.work()
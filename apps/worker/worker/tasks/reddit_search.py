"""
T031: Reddit search task
RQ background task for processing Reddit pain point discovery
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid as uuid_lib
import redis
import os

# Database imports (using relative imports from API)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../api'))

from app.database import SessionLocal
from app.models.search_run import SearchRun
from app.models.topic import Topic
from app.models.reddit_post import RedditPost
from app.models.pain_point import PainPoint
from app.services.reddit_api import RedditAPIClient

# Pipeline components
from worker.pipeline.scorer import CompositeScorer
from worker.pipeline.filter import ContentFilter
from worker.pipeline.extractor import PainPointExtractor


def process_search(search_run_id: str):
    """
    RQ task: Process Reddit pain point discovery search

    State transitions: pending → in_progress → completed/failed

    Args:
        search_run_id: UUID of search run to process

    Steps:
        1. Update status to in_progress
        2. Fetch topics from database
        3. Search Reddit using PRAW client
        4. Filter content (NSFW, spam, low-quality)
        5. Extract pain points
        6. Calculate relevance scores
        7. Save to database and Redis cache
        8. Update status to completed

    Raises:
        Exception: On failure, updates status to failed with error message
    """
    db = SessionLocal()
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=False  # Store binary for JSON
    )

    try:
        # Step 1: Load search run
        search_run = db.query(SearchRun).filter(SearchRun.id == search_run_id).first()

        if not search_run:
            raise ValueError(f"Search run {search_run_id} not found")

        # Update status to in_progress
        search_run.status = "in_progress"
        search_run.started_at = datetime.utcnow()
        db.commit()

        # Step 2: Get topics
        topics = [topic.keyword for topic in search_run.topics]

        if len(topics) == 0:
            raise ValueError("No topics associated with search run")

        print(f"Processing search {search_run_id} with topics: {topics}")

        # Step 3: Search Reddit
        reddit_client = RedditAPIClient()
        raw_posts = reddit_client.search_subreddits(
            topics=topics,
            time_range=search_run.time_range,
            limit=100,  # Max 100 posts per subreddit
            filter_nsfw=True
        )

        print(f"Fetched {len(raw_posts)} posts from Reddit")

        # Step 4: Filter content
        filtered_posts = ContentFilter.filter_posts(raw_posts, filter_nsfw=True)

        print(f"After filtering: {len(filtered_posts)} posts remain")

        if len(filtered_posts) == 0:
            # No results found, complete with 0 pain points
            search_run.status = "completed"
            search_run.completed_at = datetime.utcnow()
            search_run.pain_points_count = 0
            db.commit()
            print(f"Search {search_run_id} completed with 0 results")
            return

        # Step 5: Save Reddit posts to cache (48h TTL)
        expires_at = datetime.utcnow() + timedelta(hours=48)

        saved_posts = []
        post_ids = []  # Track post IDs for this search
        for post_data in filtered_posts:
            # Check if post already exists
            existing_post = db.query(RedditPost).filter(
                RedditPost.reddit_id == post_data["reddit_id"]
            ).first()

            if not existing_post:
                # Save new post to PostgreSQL
                reddit_post = RedditPost(
                    id=str(uuid_lib.uuid4()),
                    reddit_id=post_data["reddit_id"],
                    subreddit=post_data["subreddit"],
                    author=post_data.get("author"),
                    title=post_data["title"],
                    text=post_data.get("text"),
                    url=post_data["url"],
                    score=post_data["score"],
                    comment_count=post_data["comment_count"],
                    created_utc=post_data["created_utc"],
                    is_nsfw=post_data.get("is_nsfw", False),
                    expires_at=expires_at
                )
                db.add(reddit_post)

            saved_posts.append(post_data)
            post_ids.append(post_data["reddit_id"])

            # Save to Redis cache with 48h TTL (update even if exists)
            redis_key = f"reddit:post:{post_data['reddit_id']}"
            import json
            redis_client.setex(
                redis_key,
                172800,  # 48 hours in seconds
                json.dumps(post_data, default=str)
            )

        db.commit()

        # Track which posts belong to this search
        import json
        redis_client.setex(
            f"search:{search_run_id}:reddit_ids",
            172800,  # 48 hours
            json.dumps(post_ids)
        )

        print(f"Saved {len(saved_posts)} posts to database and Redis")

        # Step 6: Commit cached posts (unified aggregation will handle pain point extraction)
        db.commit()

        print(f"Reddit search {search_run_id} completed: {len(saved_posts)} posts cached for unified aggregation")

    except Exception as e:
        # Handle failure
        print(f"Error processing search {search_run_id}: {str(e)}")

        try:
            search_run = db.query(SearchRun).filter(SearchRun.id == search_run_id).first()
            if search_run:
                search_run.status = "failed"
                search_run.completed_at = datetime.utcnow()
                search_run.error_message = str(e)
                db.commit()
        except Exception as db_error:
            print(f"Error updating search run status: {str(db_error)}")

        raise

    finally:
        db.close()
        redis_client.close()

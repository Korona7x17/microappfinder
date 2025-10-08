"""
T017: HackerNews search task
RQ background task for HN pain point discovery
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
import logging

# Database imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../api'))

from app.database import SessionLocal
from app.models.search_run import SearchRun
from app.models.hackernews_item import HackerNewsItem
from app.services.hackernews_service import HackerNewsService

logger = logging.getLogger(__name__)


def fetch_hn_for_search(search_run_id: str):
    """
    RQ task: Fetch HackerNews items for search run

    Used as part of unified multi-source search

    Args:
        search_run_id: UUID of search run

    Steps:
        1. Load search run from database
        2. Get topics
        3. Fetch HN stories via Algolia API
        4. Store in 48h cache
        5. Update search_run.hn_items_fetched

    Returns:
        dict: Fetch statistics
    """
    db = SessionLocal()
    redis_client = None

    try:
        # Step 1: Load search run
        search_run = db.query(SearchRun).filter(SearchRun.id == search_run_id).first()

        if not search_run:
            raise ValueError(f"Search run {search_run_id} not found")

        # Step 2: Get topics
        topics = [topic.keyword for topic in search_run.topics]

        if len(topics) == 0:
            raise ValueError("No topics associated with search run")

        logger.info("Fetching HackerNews items", extra={
            "search_run_id": search_run_id,
            "topics": topics,
        })

        # Step 3: Initialize HN service
        hn_service = HackerNewsService(db_session=db)

        # Step 4: Simple HN search - just look for topics
        # Greg Isenberg approach: find what's trending first, analyze later
        # NOTE: HN Algolia index is not real-time, use longer lookback
        all_items = []
        # Map new time ranges: 1month, 3months, 6months, 1year, all
        time_range_days = {
            "1month": 30,
            "3months": 90,
            "6months": 180,
            "1year": 365,
            "all": 3650  # ~10 years
        }
        days_back = time_range_days.get(search_run.time_range, 30)

        # Search for each topic - keep it simple
        for topic in topics[:3]:  # Limit to first 3 topics
            # Search Ask HN posts (these often contain problems/requests)
            logger.info(f"HN search query (Ask HN): {topic}")
            ask_items = hn_service.fetch_and_cache_stories(
                query=topic,
                tags="ask_hn",
                min_points=2,  # Lower threshold to get more results
                days_back=days_back
            )
            all_items.extend(ask_items)

            # Also search regular stories with the topic
            logger.info(f"HN search query (Stories): {topic}")
            story_items = hn_service.fetch_and_cache_stories(
                query=topic,
                tags="story",
                min_points=5,  # Lower threshold for more results
                days_back=days_back
            )
            all_items.extend(story_items)

        # Deduplicate by hn_id
        unique_items = {item.hn_id: item for item in all_items}.values()

        logger.info("Fetched HackerNews candidates", extra={
            "search_run_id": search_run_id,
            "unique_items": len(unique_items),
        })

        # Track which HN items belong to this search
        import redis
        import json
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=False
        )

        hn_ids = [item.hn_id for item in unique_items]
        redis_client.setex(
            f"search:{search_run_id}:hn_ids",
            172800,  # 48 hours
            json.dumps(hn_ids)
        )

        # Step 5: Update search run
        search_run.hn_items_fetched = len(unique_items)
        db.commit()

        logger.info("HackerNews fetch complete", extra={
            "search_run_id": search_run_id,
            "items": len(unique_items),
        })

        return {
            "search_run_id": search_run_id,
            "items_fetched": len(unique_items),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.exception("HackerNews fetch failed", extra={
            "search_run_id": search_run_id,
        })

        # Rollback any pending transaction
        db.rollback()

        # Update search run with error (but don't fail entire search)
        if 'search_run' in locals():
            search_run.hn_items_fetched = 0
            db.commit()

        # Swallow the exception so the unified aggregation job can still run
        return {
            "search_run_id": search_run_id,
            "items_fetched": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

    finally:
        if redis_client is not None:
            try:
                redis_client.close()
            except Exception:
                pass
        db.close()

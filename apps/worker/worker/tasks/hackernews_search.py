"""
T017: HackerNews search task
RQ background task for HN pain point discovery
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

# Database imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../api'))

from app.database import SessionLocal
from app.models.search_run import SearchRun
from app.models.hackernews_item import HackerNewsItem
from app.services.hackernews_service import HackerNewsService


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

    try:
        # Step 1: Load search run
        search_run = db.query(SearchRun).filter(SearchRun.id == search_run_id).first()

        if not search_run:
            raise ValueError(f"Search run {search_run_id} not found")

        # Step 2: Get topics
        topics = [topic.keyword for topic in search_run.topics]

        if len(topics) == 0:
            raise ValueError("No topics associated with search run")

        print(f"Fetching HN items for search {search_run_id} with topics: {topics}")

        # Step 3: Initialize HN service
        hn_service = HackerNewsService(db_session=db)

        # Step 4: Fetch and cache HN stories
        # Search each topic
        all_items = []
        for topic in topics:
            items = hn_service.fetch_and_cache_stories(
                query=topic,
                tags="ask_hn",  # Focus on Ask HN for pain points
                min_points=10,  # Minimum engagement threshold
                days_back=30 if search_run.time_range == "30days" else 7
            )
            all_items.extend(items)

        # Deduplicate by hn_id
        unique_items = {item.hn_id: item for item in all_items}.values()

        print(f"Fetched {len(unique_items)} unique HN items")

        # Step 5: Update search run
        search_run.hn_items_fetched = len(unique_items)
        db.commit()

        print(f"HN fetch complete for search {search_run_id}: {len(unique_items)} items")

        return {
            "search_run_id": search_run_id,
            "items_fetched": len(unique_items),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"Error fetching HN items: {str(e)}")
        # Update search run with error (but don't fail entire search)
        if 'search_run' in locals():
            search_run.hn_items_fetched = 0
            db.commit()
        raise

    finally:
        db.close()

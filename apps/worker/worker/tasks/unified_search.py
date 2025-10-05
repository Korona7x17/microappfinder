"""
T019: Unified search aggregation task
Orchestrates multi-source search with deduplication
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid as uuid_lib
import os

# Database imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../api'))

from app.database import SessionLocal
from app.models.search_run import SearchRun
from app.models.reddit_post import RedditPost
from app.models.hackernews_item import HackerNewsItem
from app.models.pain_point import PainPoint
from app.services.unified_search_service import UnifiedSearchService
from app.services.deduplication_service import DeduplicationService

# Pipeline components
from worker.pipeline.extractor import PainPointExtractor
from textblob import TextBlob


def aggregate_and_extract_unified(search_run_id: str):
    """
    RQ task: Aggregate Reddit + HN results and extract unified pain points

    This task runs AFTER both reddit_search and hackernews_search complete

    Args:
        search_run_id: UUID of search run

    Steps:
        1. Load Reddit posts from cache
        2. Load HackerNews items from cache
        3. Run cross-source deduplication
        4. Extract pain points from unified results
        5. Calculate composite scores
        6. Save to database with proper source tracking
        7. Update search run status

    Returns:
        dict: Aggregation statistics
    """
    db = SessionLocal()

    try:
        print(f"=== Starting unified aggregation for search {search_run_id} ===")

        # Step 1: Load search run
        search_run = db.query(SearchRun).filter(SearchRun.id == search_run_id).first()

        if not search_run:
            raise ValueError(f"Search run {search_run_id} not found")

        # Step 2: Load Reddit posts (from 48h cache)
        reddit_posts = db.query(RedditPost).filter(
            RedditPost.created_utc >= search_run.created_at - timedelta(days=30),
            RedditPost.expires_at > datetime.utcnow()
        ).all()

        print(f"Loaded {len(reddit_posts)} Reddit posts")

        # Step 3: Load HackerNews items (from 48h cache)
        hn_items = db.query(HackerNewsItem).filter(
            HackerNewsItem.created_utc >= search_run.created_at - timedelta(days=30),
            HackerNewsItem.expires_at > datetime.utcnow()
        ).all()

        print(f"Loaded {len(hn_items)} HN items")

        # Step 4: Run deduplication
        dedup_service = DeduplicationService(db)
        dedup_result = dedup_service.deduplicate_cross_source(
            reddit_posts=reddit_posts,
            hn_items=hn_items
        )

        unique_items = dedup_result["unique_items"]
        duplicates = dedup_result["duplicates"]

        print(f"Deduplication: {len(unique_items)} unique items, {len(duplicates)} duplicates")

        # Step 5: Rank using unified search service
        unified_service = UnifiedSearchService(db)

        # Separate back into Reddit and HN for ranking
        reddit_for_ranking = [p for p in reddit_posts if any(p.reddit_id in item.get("source_ids", []) for item in unique_items)]
        hn_for_ranking = [i for i in hn_items if any(i.hn_id in item.get("source_ids", []) for item in unique_items)]

        ranked_results = unified_service.aggregate_and_rank(
            reddit_posts=reddit_for_ranking,
            hn_items=hn_for_ranking,
            time_range=search_run.time_range
        )

        print(f"Ranked {len(ranked_results)} unified results")

        # Step 6: Extract pain points from top results (limit to top 100)
        top_results = ranked_results[:100]
        pain_points_count = 0

        for result in top_results:
            # Extract text for pain point
            extracted_text = f"{result['title'][:200]}"
            if result.get('text'):
                extracted_text += f" - {result['text'][:300]}"

            # Trim to 500 char limit
            extracted_text = extracted_text[:500]

            # Create pain point with proper source tracking
            pain_point = PainPoint(
                id=str(uuid_lib.uuid4()),
                search_run_id=search_run.id,
                extracted_text=extracted_text,
                relevance_score=round(result['composite_score'], 4),
                sentiment_score=round(
                    -TextBlob(f"{result.get('title', '')} {result.get('text', '')}").sentiment.polarity,
                    2
                ),
                source_platform=result['source'],  # Feature 002: Multi-source
                source_post_ids=[result['id']],  # Feature 002: Platform-agnostic IDs
                source_deleted=False
            )

            db.add(pain_point)
            pain_points_count += 1

        # Step 7: Update search run
        search_run.status = "completed"
        search_run.completed_at = datetime.utcnow()
        search_run.pain_points_count = pain_points_count

        db.commit()

        print(f"=== Unified aggregation complete: {pain_points_count} pain points ===")

        return {
            "search_run_id": search_run_id,
            "reddit_posts": len(reddit_posts),
            "hn_items": len(hn_items),
            "unique_items": len(unique_items),
            "duplicates": len(duplicates),
            "pain_points": pain_points_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"Error in unified aggregation: {str(e)}")

        # Update search run status to failed
        try:
            search_run = db.query(SearchRun).filter(SearchRun.id == search_run_id).first()
            if search_run:
                search_run.status = "failed"
                search_run.completed_at = datetime.utcnow()
                search_run.error_message = f"Unified aggregation failed: {str(e)}"
                db.commit()
        except Exception as db_error:
            print(f"Error updating search run: {str(db_error)}")

        raise

    finally:
        db.close()

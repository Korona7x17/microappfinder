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

# Feature 003: AI-powered opportunity detection
from app.services.opportunity_filter_service import OpportunityFilterService
from app.services.llm_analysis_service import LLMAnalysisService


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
    import redis
    import json

    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )

    try:
        print(f"=== Starting unified aggregation for search {search_run_id} ===")

        # Step 1: Load search run
        search_run = db.query(SearchRun).filter(SearchRun.id == search_run_id).first()

        if not search_run:
            raise ValueError(f"Search run {search_run_id} not found")

        # Step 2: Load Reddit posts for THIS search only
        reddit_ids_json = redis_client.get(f"search:{search_run_id}:reddit_ids")
        reddit_ids = json.loads(reddit_ids_json) if reddit_ids_json else []

        reddit_posts = db.query(RedditPost).filter(
            RedditPost.reddit_id.in_(reddit_ids)
        ).all() if reddit_ids else []

        print(f"Loaded {len(reddit_posts)} Reddit posts for this search")

        # Step 3: Load HackerNews items for THIS search only
        hn_ids_json = redis_client.get(f"search:{search_run_id}:hn_ids")
        hn_ids = json.loads(hn_ids_json) if hn_ids_json else []

        hn_items = db.query(HackerNewsItem).filter(
            HackerNewsItem.hn_id.in_(hn_ids)
        ).all() if hn_ids else []

        print(f"Loaded {len(hn_items)} HN items for this search")

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

        # Pass all items to ranking (deduplication is for tracking only)
        # Don't pass time_range - items are already time-filtered when fetched
        ranked_results = unified_service.aggregate_and_rank(
            reddit_posts=reddit_posts,
            hn_items=hn_items
        )

        print(f"Ranked {len(ranked_results)} unified results")

        # Step 6: AI-powered opportunity detection (Feature 003)
        # Pipeline: Pre-filter → LLM Analysis → Store top 5

        # Step 6a: Pre-filter candidates - be VERY lenient per spec
        # The spec emphasizes capturing MORE opportunities, not filtering them out

        # IMPORTANT: Always ensure we have candidates for analysis
        # Even if no Reddit posts, we should process HN items and vice versa
        all_candidates = []

        # If ranked_results is empty, try to create candidates from raw items
        if not ranked_results:
            print("WARNING: ranked_results is empty, creating candidates from raw items")

            # Convert Reddit posts to candidate format
            for post in reddit_posts:
                all_candidates.append({
                    'id': post.reddit_id,
                    'source': 'reddit',
                    'title': post.title,
                    'text': post.selftext,
                    'url': post.url,
                    'score': post.score,
                    'num_comments': post.num_comments,
                    'created_utc': post.created_utc,
                    'composite_score': 0.1  # Default low score
                })

            # Convert HN items to candidate format
            for item in hn_items:
                all_candidates.append({
                    'id': str(item.hn_id),
                    'source': 'hackernews',
                    'title': item.title,
                    'text': item.text or '',
                    'url': item.url or f"https://news.ycombinator.com/item?id={item.hn_id}",
                    'score': item.points,
                    'num_comments': item.comment_count,
                    'created_at': item.created_at.timestamp() if hasattr(item.created_at, 'timestamp') else 0,
                    'composite_score': 0.1  # Default low score
                })
        else:
            all_candidates = ranked_results

        # Apply VERY lenient filter per spec - focus on finding pain signals
        if len(all_candidates) <= 20:
            # Pass all to LLM if we have 20 or fewer
            filtered_candidates = all_candidates
            print(f"Passing all {len(all_candidates)} candidates to LLM (≤20 threshold)")
        else:
            # Use MUCH more lenient thresholds per spec
            filter_service = OpportunityFilterService()
            filtered_candidates = filter_service.filter_candidates(
                candidates=all_candidates,
                min_comments=0,  # Accept all - let LLM decide
                min_score=0      # Accept all scores - let LLM decide
            )

            filter_stats = filter_service.get_filter_stats(
                original_count=len(all_candidates),
                filtered_count=len(filtered_candidates)
            )

            print(f"Pre-filter: {filter_stats['original_count']} → {filter_stats['filtered_count']} candidates ({filter_stats['reduction_percentage']}% reduction)")

            # Ensure we always have at least 20 candidates for LLM
            if len(filtered_candidates) < 20 and len(all_candidates) > 20:
                filtered_candidates = all_candidates[:20]
                print(f"Filter reduced too much, taking top 20 for LLM analysis")

        # Step 6b: Run two-tier LLM analysis
        pain_points_count = 0

        if filtered_candidates:
            try:
                llm_service = LLMAnalysisService()
                top_opportunities = llm_service.analyze_opportunities(
                    candidates=filtered_candidates,
                    tier1_limit=10,  # GPT-4o-mini selects top 10
                    tier2_limit=999  # No limit - Claude decides how many
                )

                print(f"LLM analysis: Selected {len(top_opportunities)} top opportunities")

                # Step 6c: Store top opportunities with LLM insights
                for opportunity in top_opportunities:
                    # Extract full text (up to 2000 chars)
                    extracted_text = f"{opportunity['title'][:500]}"
                    if opportunity.get('text'):
                        extracted_text += f" - {opportunity['text'][:1500]}"
                    extracted_text = extracted_text[:2000]

                    # Get LLM insights
                    llm_analysis = opportunity.get('llm_analysis', {})

                    # Create pain point with LLM insights
                    pain_point = PainPoint(
                        id=str(uuid_lib.uuid4()),
                        search_run_id=search_run.id,
                        extracted_text=llm_analysis.get('problem_summary', extracted_text),
                        relevance_score=round(opportunity['composite_score'], 4),
                        sentiment_score=round(
                            -TextBlob(f"{opportunity.get('title', '')} {opportunity.get('text', '')}").sentiment.polarity,
                            2
                        ),
                        source_platform=opportunity['source'],
                        source_post_ids=[opportunity['id']],
                        source_deleted=False,
                        llm_insights=llm_analysis  # Store full LLM analysis
                    )

                    db.add(pain_point)
                    pain_points_count += 1

            except Exception as llm_error:
                print(f"LLM analysis failed: {str(llm_error)}")
                print("Falling back to all filtered candidates")

                # Fallback: Store all filtered candidates without LLM insights
                for result in filtered_candidates:
                    extracted_text = f"{result['title'][:500]}"
                    if result.get('text'):
                        extracted_text += f" - {result['text'][:1500]}"
                    extracted_text = extracted_text[:2000]

                    pain_point = PainPoint(
                        id=str(uuid_lib.uuid4()),
                        search_run_id=search_run.id,
                        extracted_text=extracted_text,
                        relevance_score=round(result['composite_score'], 4),
                        sentiment_score=round(
                            -TextBlob(f"{result.get('title', '')} {result.get('text', '')}").sentiment.polarity,
                            2
                        ),
                        source_platform=result['source'],
                        source_post_ids=[result['id']],
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
        redis_client.close()

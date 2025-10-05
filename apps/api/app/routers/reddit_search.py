"""
T028: Reddit search endpoints
Reddit pain point discovery endpoints per contracts/openapi.yaml
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, and_
from typing import Optional
from datetime import datetime, timedelta
import uuid as uuid_lib

from app.database import get_db
from app.models.user import User
from app.models.topic import Topic
from app.models.search_run import SearchRun, search_run_topics
from app.models.pain_point import PainPoint
from app.schemas.search import (
    SearchRequest,
    SearchRunCreated,
    SearchRunStatus,
    PaginatedPainPoints,
    UserDashboard,
    RecentSearchRun
)
from app.schemas.pain_point import PainPointResponse
from app.core.auth import get_current_user, verify_run_ownership


router = APIRouter(prefix="/api/reddit", tags=["reddit_search"])


@router.post("/search", response_model=SearchRunCreated, status_code=status.HTTP_201_CREATED)
async def create_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    POST /api/reddit/search

    Initiate Reddit pain point discovery search

    Returns:
        - 201: Search run created and enqueued
        - 401: Not authenticated
        - 422: Validation error (invalid topics or time_range)
    """
    # Create search run
    search_run = SearchRun(
        id=str(uuid_lib.uuid4()),
        user_id=current_user.id,
        status="pending",
        time_range=request.time_range.value
    )

    db.add(search_run)
    db.flush()  # Get ID before commit

    # Create/reuse topics and associate with search run
    for topic_keyword in request.topics:
        # Check if topic exists
        topic = db.query(Topic).filter(Topic.keyword == topic_keyword).first()

        if not topic:
            # Create new topic
            topic = Topic(
                id=str(uuid_lib.uuid4()),
                keyword=topic_keyword,
                search_count=1
            )
            db.add(topic)
        else:
            # Increment search count
            topic.search_count += 1

        db.flush()

        # Associate topic with search run
        db.execute(
            search_run_topics.insert().values(
                search_run_id=search_run.id,
                topic_id=topic.id
            )
        )

    db.commit()
    db.refresh(search_run)

    # TODO: Enqueue RQ job for background processing (T031)
    # from app.worker.tasks.reddit_search import process_search
    # job = process_search.delay(search_run.id)

    return SearchRunCreated(
        search_run_id=str(search_run.id),
        status=search_run.status,
        message="Search started successfully"
    )


@router.get("/search/{search_run_id}", response_model=SearchRunStatus, status_code=status.HTTP_200_OK)
async def get_search_status(
    search_run: SearchRun = Depends(verify_run_ownership),
    db: Session = Depends(get_db)
):
    """
    GET /api/reddit/search/{search_run_id}

    Get search run status and metadata

    Returns:
        - 200: Search run status
        - 401: Not authenticated
        - 403: Not authorized to access this search run
        - 404: Search run not found
    """
    # Load topics
    topics = [topic.keyword for topic in search_run.topics]

    return SearchRunStatus(
        search_run_id=str(search_run.id),
        status=search_run.status,
        topics=topics,
        time_range=search_run.time_range,
        created_at=search_run.created_at,
        started_at=search_run.started_at,
        completed_at=search_run.completed_at,
        pain_points_count=search_run.pain_points_count,
        error_message=search_run.error_message
    )


@router.get("/search/{search_run_id}/results", response_model=PaginatedPainPoints)
async def get_search_results(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    search_run: SearchRun = Depends(verify_run_ownership),
    db: Session = Depends(get_db)
):
    """
    GET /api/reddit/search/{search_run_id}/results

    Get paginated pain points for completed search

    Returns:
        - 200: Pain points list (if completed)
        - 202: Still processing (if pending/in_progress)
        - 401: Not authenticated
        - 403: Not authorized
        - 404: Search run not found
        - 500: Search failed
    """
    # Check status
    if search_run.status == "pending":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "status": "pending",
                "message": "Search has not started yet"
            }
        )

    if search_run.status == "in_progress":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "status": "in_progress",
                "message": "Search is still processing"
            }
        )

    if search_run.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "failed",
                "error_message": search_run.error_message
            }
        )

    # Get total count
    total = db.query(PainPoint).filter(
        PainPoint.search_run_id == search_run.id
    ).count()

    # Get paginated pain points (sorted by relevance_score DESC)
    offset = (page - 1) * limit
    pain_points = db.query(PainPoint).filter(
        PainPoint.search_run_id == search_run.id
    ).order_by(desc(PainPoint.relevance_score)).offset(offset).limit(limit).all()

    # Get topics for each pain point (from parent search run)
    topics = [topic.keyword for topic in search_run.topics]

    # Convert to response models
    pain_point_responses = [
        PainPointResponse(
            id=str(pp.id),
            extracted_text=pp.extracted_text,
            relevance_score=float(pp.relevance_score),
            sentiment_score=float(pp.sentiment_score),
            source_reddit_post_ids=pp.source_reddit_post_ids,
            source_deleted=pp.source_deleted,
            created_at=pp.created_at,
            topics=topics
        )
        for pp in pain_points
    ]

    return PaginatedPainPoints(
        search_run_id=str(search_run.id),
        status=search_run.status,
        pain_points=pain_point_responses,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/recent", response_model=PaginatedPainPoints, status_code=status.HTTP_200_OK)
async def get_recent_pain_points(
    limit: int = Query(20, ge=1, le=50, description="Items to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GET /api/reddit/recent

    Get recent pain points from last 7 days (fallback/discovery endpoint)

    Returns:
        - 200: Recent pain points list
        - 401: Not authenticated
    """
    # Get pain points from last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    pain_points = db.query(PainPoint).join(
        SearchRun
    ).filter(
        and_(
            PainPoint.created_at >= seven_days_ago,
            PainPoint.source_deleted == False,  # Exclude deleted sources
            SearchRun.status == "completed"
        )
    ).order_by(desc(PainPoint.relevance_score)).limit(limit).all()

    # Convert to response models
    pain_point_responses = []
    for pp in pain_points:
        # Get topics from search run
        search_run = db.query(SearchRun).filter(SearchRun.id == pp.search_run_id).first()
        topics = [topic.keyword for topic in search_run.topics] if search_run else []

        pain_point_responses.append(
            PainPointResponse(
                id=str(pp.id),
                extracted_text=pp.extracted_text,
                relevance_score=float(pp.relevance_score),
                sentiment_score=float(pp.sentiment_score),
                source_reddit_post_ids=pp.source_reddit_post_ids,
                source_deleted=pp.source_deleted,
                created_at=pp.created_at,
                topics=topics
            )
        )

    message = None
    if len(pain_point_responses) == 0:
        message = "No recent pain points found. Start a search to discover opportunities!"

    return PaginatedPainPoints(
        search_run_id="recent",  # Special ID for recent endpoint
        status="completed",
        pain_points=pain_point_responses,
        total=len(pain_point_responses),
        page=1,
        limit=limit,
        message=message
    )


@router.get("/dashboard", response_model=UserDashboard, status_code=status.HTTP_200_OK)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GET /api/reddit/dashboard

    Get user dashboard with recent searches and pain points

    Returns:
        - 200: Dashboard data
        - 401: Not authenticated
    """
    # Get last 10 search runs
    recent_runs = db.query(SearchRun).filter(
        SearchRun.user_id == current_user.id
    ).order_by(desc(SearchRun.created_at)).limit(10).all()

    # Convert to response models
    recent_runs_response = [
        RecentSearchRun(
            search_run_id=str(sr.id),
            status=sr.status,
            topics=[t.keyword for t in sr.topics],
            created_at=sr.created_at,
            pain_points_count=sr.pain_points_count
        )
        for sr in recent_runs
    ]

    # Get total searches count
    total_searches = db.query(SearchRun).filter(
        SearchRun.user_id == current_user.id
    ).count()

    # Get recent pain points (last 7 days) as fallback preview
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_pain_points = db.query(PainPoint).join(
        SearchRun
    ).filter(
        and_(
            PainPoint.created_at >= seven_days_ago,
            PainPoint.source_deleted == False,
            SearchRun.status == "completed"
        )
    ).order_by(desc(PainPoint.relevance_score)).limit(20).all()

    # Convert to response models
    pain_point_responses = []
    for pp in recent_pain_points:
        search_run = db.query(SearchRun).filter(SearchRun.id == pp.search_run_id).first()
        topics = [topic.keyword for topic in search_run.topics] if search_run else []

        pain_point_responses.append(
            PainPointResponse(
                id=str(pp.id),
                extracted_text=pp.extracted_text,
                relevance_score=float(pp.relevance_score),
                sentiment_score=float(pp.sentiment_score),
                source_reddit_post_ids=pp.source_reddit_post_ids,
                source_deleted=pp.source_deleted,
                created_at=pp.created_at,
                topics=topics
            )
        )

    return UserDashboard(
        recent_runs=recent_runs_response,
        total_searches=total_searches,
        recent_pain_points=pain_point_responses
    )

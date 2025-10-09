"""
T009/T010: Opportunities API router
List and detail endpoints for opportunities with filtering and pagination
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Literal, List
from pydantic import BaseModel, Field
import uuid as uuid_lib

from app.core.database import get_db
from app.models import OpportunityResponse, OpportunityDetail
from app.services.opportunity_service import OpportunityService

router = APIRouter()


class OpportunitiesListResponse(BaseModel):
    """Response model for list endpoint"""
    opportunities: List[OpportunityResponse]
    next_cursor: Optional[str] = None
    has_more: bool


@router.get("", response_model=OpportunitiesListResponse)
async def list_opportunities(
    severity_min: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum problem severity (0-10)"),
    severity_max: Optional[float] = Query(None, ge=0.0, le=10.0, description="Maximum problem severity (0-10)"),
    market_size: Optional[Literal["niche", "mid", "large"]] = Query(None, description="Market size filter"),
    competition_level: Optional[Literal["low", "medium", "high", "saturated"]] = Query(None, description="Competition level filter"),
    trend_direction: Optional[Literal["declining", "stable", "growing", "explosive"]] = Query(None, description="Trend direction filter"),
    sort_by: Literal["severity", "monetization", "analyzed_at"] = Query("analyzed_at", description="Sort field"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    limit: int = Query(12, ge=1, le=50, description="Results per page (1-50)"),
    db: Session = Depends(get_db)
):
    """
    List opportunities with filtering, sorting, and cursor pagination

    - **severity_min/max**: Filter by problem severity (0-10 scale)
    - **market_size**: Filter by market size (niche/mid/large)
    - **competition_level**: Filter by competition (low/medium/high/saturated)
    - **trend_direction**: Filter by trend (declining/stable/growing/explosive)
    - **sort_by**: Sort field (severity/monetization/analyzed_at)
    - **sort_order**: Sort direction (asc/desc)
    - **cursor**: Pagination cursor (from previous response)
    - **limit**: Results per page (default 12, max 50)
    """
    service = OpportunityService(db)

    result = service.list_opportunities(
        severity_min=severity_min,
        severity_max=severity_max,
        market_size=market_size,
        competition_level=competition_level,
        trend_direction=trend_direction,
        sort_by=sort_by,
        sort_order=sort_order,
        cursor=cursor,
        limit=limit
    )

    return OpportunitiesListResponse(
        opportunities=[OpportunityResponse.model_validate(opp) for opp in result['opportunities']],
        next_cursor=result['next_cursor'],
        has_more=result['has_more']
    )


@router.get("/{opportunity_id}", response_model=OpportunityDetail)
async def get_opportunity_detail(
    opportunity_id: str,
    db: Session = Depends(get_db)
):
    """
    Get full details for a single opportunity

    Returns complete opportunity data including:
    - All six-dimensional scores
    - Trend data (if available)
    - Geographic spread (if available)
    - Affected industries (if available)
    - Enrichment metadata
    """
    service = OpportunityService(db)

    # Validate UUID format
    try:
        uuid_obj = uuid_lib.UUID(opportunity_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID format")

    opportunity = service.get_opportunity_by_id(str(uuid_obj))

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return OpportunityDetail.model_validate(opportunity)

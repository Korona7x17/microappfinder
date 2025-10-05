"""
T022: Search request/response schemas
Pydantic models for Reddit search endpoints per contracts/openapi.yaml
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional, Literal
from enum import Enum
import re


class TimeRangeEnum(str, Enum):
    """Valid time range values"""
    HOUR_24 = "24h"
    DAYS_7 = "7days"
    DAYS_30 = "30days"
    DAYS_90 = "90days"
    YEAR_1 = "1year"
    ALL = "all"


class SearchStatusEnum(str, Enum):
    """Valid search run status values"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchRequest(BaseModel):
    """Request body for POST /api/reddit/search"""
    topics: List[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Search keywords/phrases (1-5 items, 2-100 chars each)"
    )
    time_range: TimeRangeEnum = Field(
        ...,
        description="Time window for Reddit search"
    )

    @validator("topics")
    def validate_topics(cls, v):
        """Validate topic keywords"""
        for topic in v:
            # Check length
            if len(topic) < 2 or len(topic) > 100:
                raise ValueError(f"Topic must be 2-100 characters: '{topic}'")

            # Check characters (alphanumeric + spaces only)
            if not re.match(r"^[a-zA-Z0-9\s]+$", topic):
                raise ValueError(f"Topic can only contain alphanumeric characters and spaces: '{topic}'")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "topics": ["productivity tools", "time management"],
                "time_range": "7days"
            }
        }


class SearchRunCreated(BaseModel):
    """Response for POST /api/reddit/search"""
    search_run_id: str = Field(..., description="UUID of created search run")
    status: SearchStatusEnum = Field(..., description="Initial status (pending or in_progress)")
    message: str = Field(default="Search started successfully")

    class Config:
        json_schema_extra = {
            "example": {
                "search_run_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "message": "Search started successfully"
            }
        }


class SearchRunStatus(BaseModel):
    """Response for GET /api/reddit/search/{search_run_id}"""
    search_run_id: str = Field(..., description="UUID of search run")
    status: SearchStatusEnum = Field(..., description="Current status")
    topics: List[str] = Field(..., description="Search topics")
    time_range: TimeRangeEnum = Field(..., description="Time range")
    created_at: datetime = Field(..., description="Run creation time")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    pain_points_count: int = Field(default=0, description="Total pain points extracted")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    # Feature 002: Multi-source tracking
    sources_queried: List[str] = Field(default=["reddit"], description="Sources queried (reddit, hackernews, etc.)")
    hn_items_fetched: Optional[int] = Field(None, description="HackerNews items fetched (null if not queried)")

    class Config:
        json_schema_extra = {
            "example": {
                "search_run_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "topics": ["productivity tools"],
                "time_range": "7days",
                "created_at": "2025-10-04T12:00:00Z",
                "started_at": "2025-10-04T12:00:05Z",
                "completed_at": "2025-10-04T12:00:25Z",
                "pain_points_count": 15,
                "error_message": None
            }
        }


class PaginatedPainPoints(BaseModel):
    """Response for GET /api/reddit/search/{search_run_id}/results"""
    search_run_id: str = Field(..., description="UUID of search run")
    status: SearchStatusEnum = Field(..., description="Search run status")
    pain_points: List["PainPointResponse"] = Field(default_factory=list, description="List of pain points")
    total: int = Field(default=0, description="Total pain points count")
    page: int = Field(default=1, description="Current page number")
    limit: int = Field(default=50, description="Items per page")
    message: Optional[str] = Field(None, description="Status message (e.g., 'still processing')")

    class Config:
        json_schema_extra = {
            "example": {
                "search_run_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "pain_points": [],
                "total": 15,
                "page": 1,
                "limit": 50,
                "message": None
            }
        }


class RecentSearchRun(BaseModel):
    """Recent search run summary for dashboard"""
    search_run_id: str
    status: SearchStatusEnum
    topics: List[str]
    created_at: datetime
    pain_points_count: int


class UserDashboard(BaseModel):
    """Response for GET /api/reddit/dashboard"""
    recent_runs: List[RecentSearchRun] = Field(
        default_factory=list,
        description="Last 10 search runs"
    )
    total_searches: int = Field(default=0, description="Total searches count")
    recent_pain_points: List["PainPointResponse"] = Field(
        default_factory=list,
        description="Top 20 recent pain points (fallback preview)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "recent_runs": [],
                "total_searches": 5,
                "recent_pain_points": []
            }
        }


# Import PainPointResponse for type hints
from .pain_point import PainPointResponse

# Update forward references
PaginatedPainPoints.model_rebuild()
UserDashboard.model_rebuild()

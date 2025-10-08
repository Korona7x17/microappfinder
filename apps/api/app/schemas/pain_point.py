"""
T023: PainPoint schema
Pydantic model for pain point responses per contracts/openapi.yaml
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal


class PainPointResponse(BaseModel):
    """Response schema for pain point data"""
    id: str = Field(..., description="UUID of pain point")
    extracted_text: str = Field(
        ...,
        max_length=10000,
        description="Summarized pain point (max 10000 chars)"
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Composite score (0-1): 0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment"
    )
    sentiment_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Sentiment polarity (-1 to 1) from TextBlob"
    )
    llm_insights: Optional[Dict[str, Any]] = Field(
        default=None,
        description="LLM-generated opportunity insights (problem_summary, why_good_opportunity, key_quotes, scores)"
    )
    source_platform: str = Field(
        default="reddit",
        description="Source platform (reddit, hackernews, etc.)"
    )
    source_post_ids: List[str] = Field(
        default_factory=list,
        description="Array of source post IDs (e.g., ['t3_abc123'] for Reddit, ['12345678'] for HN)"
    )
    source_deleted: bool = Field(
        default=False,
        description="Flag if source posts were deleted from source platform"
    )
    created_at: datetime = Field(..., description="Extraction timestamp")
    topics: List[str] = Field(
        default_factory=list,
        description="Associated topics from parent search run"
    )

    @validator("extracted_text")
    def validate_extracted_text_length(cls, v):
        """Ensure extracted text doesn't exceed 10000 chars"""
        if len(v) > 10000:
            raise ValueError("Extracted text must not exceed 10000 characters")
        return v

    @validator("relevance_score", "sentiment_score")
    def validate_score_precision(cls, v):
        """Round scores to appropriate precision"""
        if isinstance(v, Decimal):
            return float(v)
        return round(v, 4) if v is not None else v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "extracted_text": "Users struggle with time management and need better productivity tracking tools",
                "relevance_score": 0.8542,
                "sentiment_score": -0.35,
                "source_platform": "reddit",
                "source_post_ids": ["t3_abc123", "t3_def456"],
                "source_deleted": False,
                "created_at": "2025-10-04T12:00:30Z",
                "topics": ["productivity tools", "time management"]
            }
        }


class RecentPainPointResponse(BaseModel):
    """Simplified pain point for /api/reddit/recent endpoint"""
    id: str
    extracted_text: str
    relevance_score: float
    sentiment_score: float
    created_at: datetime
    topics: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "extracted_text": "Need better project management tools for remote teams",
                "relevance_score": 0.9123,
                "sentiment_score": -0.42,
                "created_at": "2025-10-04T12:00:30Z",
                "topics": ["project management"]
            }
        }

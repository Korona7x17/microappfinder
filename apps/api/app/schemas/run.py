from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RunCreate(BaseModel):
    """Schema for creating a new run"""
    topics: List[str]
    depth: str = "standard"  # "quick" or "standard"


class RunResponse(BaseModel):
    """Schema for run response"""
    id: str
    user_id: str
    topic_tags: List[str]
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    counters: dict = {}
    cost_estimate_cents: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

"""
Shared Python schemas for MicroAppFinder
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class Source(str, Enum):
    REDDIT = "reddit"
    HN = "hn"
    PRODUCTHUNT = "producthunt"
    INDIEHACKERS = "indiehackers"


class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    IRREGULAR = "irregular"


class WTPHint(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SignalBase(BaseModel):
    source: Source
    url: str
    audience_guess: Optional[str] = None
    job_to_be_done: Optional[str] = None
    pain_snippet: Optional[str] = None
    frequency: Optional[Frequency] = None
    evidence_pull: bool = False
    workaround: Optional[str] = None
    wtp_hint: WTPHint = WTPHint.NONE
    metrics: Dict[str, Any] = {}
    confidence: float = 0.5
    micro_fit: bool = True


class SignalCreate(SignalBase):
    run_id: str


class SignalResponse(SignalBase):
    id: str
    run_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

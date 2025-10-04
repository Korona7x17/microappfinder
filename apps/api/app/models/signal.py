from sqlalchemy import Column, String, Text, Boolean, JSON, TIMESTAMP, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class Source(str, enum.Enum):
    REDDIT = "reddit"
    HN = "hn"
    PRODUCTHUNT = "producthunt"
    INDIEHACKERS = "indiehackers"


class Frequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    IRREGULAR = "irregular"


class WTPHint(str, enum.Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Signal(Base):
    __tablename__ = "signals"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(Enum(Source), nullable=False)
    url = Column(Text, nullable=False)
    audience_guess = Column(Text, nullable=True)
    job_to_be_done = Column(Text, nullable=True)
    pain_snippet = Column(Text, nullable=True)
    frequency = Column(Enum(Frequency), nullable=True)
    evidence_pull = Column(Boolean, default=False)
    workaround = Column(Text, nullable=True)
    wtp_hint = Column(Enum(WTPHint), default=WTPHint.NONE)
    metrics = Column(JSON, default=dict)
    confidence = Column(Float, default=0.5)
    micro_fit = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    run = relationship("Run", back_populates="signals")

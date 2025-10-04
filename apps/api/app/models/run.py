from sqlalchemy import Column, String, Integer, TIMESTAMP, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    topic_tags = Column(JSON, nullable=False)
    status = Column(Enum(RunStatus), default=RunStatus.PENDING, nullable=False)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    counters = Column(JSON, default=dict)
    cost_estimate_cents = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    signals = relationship("Signal", back_populates="run", cascade="all, delete-orphan")
    clusters = relationship("Cluster", back_populates="run", cascade="all, delete-orphan")
    briefs = relationship("Brief", back_populates="run", cascade="all, delete-orphan")

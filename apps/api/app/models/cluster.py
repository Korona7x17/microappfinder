from sqlalchemy import Column, String, Text, Integer, Float, JSON, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    theme = Column(Text, nullable=False)
    audiences = Column(ARRAY(String), default=list)
    signals_count = Column(Integer, default=0)
    pain_intensity_avg = Column(Float, default=0.0)
    frequency_mode = Column(String, nullable=True)
    pull_evidence = Column(Text, nullable=True)
    gap_summary = Column(Text, nullable=True)
    score_int = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    run = relationship("Run", back_populates="clusters")
    briefs = relationship("Brief", back_populates="cluster", cascade="all, delete-orphan")

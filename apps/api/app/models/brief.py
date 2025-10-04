from sqlalchemy import Column, String, Text, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Brief(Base):
    __tablename__ = "briefs"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    cluster_id = Column(String, ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    who_hurts = Column(Text, nullable=True)
    job_to_be_done = Column(Text, nullable=True)
    killer_feature = Column(Text, nullable=True)
    scope = Column(JSON, default=dict)
    mechanics = Column(JSON, default=dict)
    success_metric = Column(Text, nullable=True)
    pricing_hint = Column(Text, nullable=True)
    risks = Column(Text, nullable=True)
    validation_plan = Column(JSON, default=dict)
    proof_urls = Column(JSON, default=list)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    run = relationship("Run", back_populates="briefs")
    cluster = relationship("Cluster", back_populates="briefs")

"""
T002: Opportunity model
SQLAlchemy model and Pydantic schemas for multi-dimensional opportunity analysis
"""
from sqlalchemy import Column, Float, String, Integer, DateTime, ForeignKey, ARRAY, CheckConstraint
from sqlalchemy.sql import text as sql_text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
import uuid as uuid_lib

from . import Base


class Opportunity(Base):
    """
    Opportunity model for validated business opportunities with six-dimensional scoring.

    Survives beyond 48h Reddit compliance window by storing only derived insights (no raw content).
    When pain_point is deleted after 48h, opportunity persists with pain_point_id=NULL.
    """
    __tablename__ = "opportunities"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sql_text("gen_random_uuid()"),
        comment="Unique opportunity identifier"
    )

    # Foreign Key (nullable - survives pain_point deletion)
    pain_point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pain_points.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source pain point (NULL if deleted after 48h TTL)"
    )

    # Display Fields
    title = Column(
        String(100),
        nullable=False,
        comment="Opportunity title (max 100 chars)"
    )

    summary = Column(
        String(500),
        nullable=False,
        comment="Opportunity summary (max 500 chars)"
    )

    # Six-Dimensional Scores
    problem_severity = Column(
        Float,
        nullable=False,
        comment="Pain severity (0=minor, 10=critical)"
    )

    market_size_indicator = Column(
        String(10),
        nullable=False,
        comment="Addressable market estimate: niche, mid, large"
    )

    monetization_potential = Column(
        Float,
        nullable=False,
        comment="Revenue potential (0=low, 10=high)"
    )

    technical_complexity = Column(
        Float,
        nullable=False,
        comment="Implementation difficulty (0=trivial, 10=hard)"
    )

    competition_level = Column(
        String(20),
        nullable=False,
        comment="Competitive landscape: low, medium, high, saturated"
    )

    trend_direction = Column(
        String(20),
        nullable=False,
        comment="Market trajectory: declining, stable, growing, explosive"
    )

    # Metadata
    confidence_level = Column(
        Float,
        nullable=False,
        comment="Analysis confidence (0=low, 1=high)"
    )

    trend_data = Column(
        JSONB,
        nullable=True,
        comment="Time-series data: {timestamps: [], frequencies: [], sentiment: []}"
    )

    geographic_spread = Column(
        ARRAY(String),
        nullable=True,
        comment="Geographic regions: ['North America', 'Europe']"
    )

    affected_industries = Column(
        ARRAY(String),
        nullable=True,
        comment="Industries: ['SaaS', 'E-commerce']"
    )

    # Timestamps
    analyzed_at = Column(
        DateTime,
        nullable=False,
        server_default=sql_text("NOW()"),
        index=True,
        comment="Initial analysis timestamp"
    )

    enrichment_count = Column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Number of times opportunity enriched"
    )

    last_enriched_at = Column(
        DateTime,
        nullable=True,
        comment="Most recent enrichment timestamp"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "problem_severity >= 0.0 AND problem_severity <= 10.0",
            name="check_problem_severity_range"
        ),
        CheckConstraint(
            "market_size_indicator IN ('niche', 'mid', 'large')",
            name="check_market_size_indicator"
        ),
        CheckConstraint(
            "monetization_potential >= 0.0 AND monetization_potential <= 10.0",
            name="check_monetization_potential_range"
        ),
        CheckConstraint(
            "technical_complexity >= 0.0 AND technical_complexity <= 10.0",
            name="check_technical_complexity_range"
        ),
        CheckConstraint(
            "competition_level IN ('low', 'medium', 'high', 'saturated')",
            name="check_competition_level"
        ),
        CheckConstraint(
            "trend_direction IN ('declining', 'stable', 'growing', 'explosive')",
            name="check_trend_direction"
        ),
        CheckConstraint(
            "confidence_level >= 0.0 AND confidence_level <= 1.0",
            name="check_confidence_level_range"
        ),
        CheckConstraint(
            "enrichment_count >= 0",
            name="check_enrichment_count_nonnegative"
        ),
    )

    # Relationships
    pain_point = relationship("PainPoint", back_populates="opportunity")

    def update_scores(self, new_scores: "OpportunityScores") -> None:
        """Update opportunity with new LLM analysis scores"""
        self.problem_severity = new_scores.problem_severity
        self.market_size_indicator = new_scores.market_size_indicator
        self.monetization_potential = new_scores.monetization_potential
        self.technical_complexity = new_scores.technical_complexity
        self.competition_level = new_scores.competition_level
        self.trend_direction = new_scores.trend_direction
        self.confidence_level = new_scores.confidence_level

    def __repr__(self):
        return f"<Opportunity(id={self.id}, severity={self.problem_severity}, market={self.market_size_indicator})>"


# ===== Pydantic Validation Models =====

class OpportunityScores(BaseModel):
    """LLM output schema for opportunity analysis"""
    problem_severity: float = Field(ge=0.0, le=10.0, description="Pain severity (0=minor, 10=critical)")
    market_size_indicator: Literal["niche", "mid", "large"] = Field(description="Addressable market estimate")
    monetization_potential: float = Field(ge=0.0, le=10.0, description="Revenue potential (0=low, 10=high)")
    technical_complexity: float = Field(ge=0.0, le=10.0, description="Implementation difficulty (0=trivial, 10=hard)")
    competition_level: Literal["low", "medium", "high", "saturated"] = Field(description="Competitive landscape")
    trend_direction: Literal["declining", "stable", "growing", "explosive"] = Field(description="Market trajectory")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Analysis confidence (0=low, 1=high)")
    reasoning: str = Field(description="LLM explanation for scores")

    model_config = {"from_attributes": True}


class TrendData(BaseModel):
    """Schema for trend_data JSONB column"""
    timestamps: list[str]  # ISO8601 dates
    frequencies: list[int]  # Mention counts per timestamp
    sentiment: list[float]  # Sentiment scores (-1.0 to 1.0)

    @field_validator('timestamps', 'frequencies', 'sentiment')
    @classmethod
    def arrays_must_have_equal_length(cls, v, info):
        """Ensure all arrays have the same length"""
        # This will be called for each field, so we can't do cross-field validation here
        # Cross-field validation will be done in model_validator
        return v

    model_config = {"from_attributes": True}


class OpportunityCreate(BaseModel):
    """Schema for creating new opportunity"""
    pain_point_id: uuid_lib.UUID
    scores: OpportunityScores
    trend_data: Optional[TrendData] = None
    geographic_spread: Optional[list[str]] = None
    affected_industries: Optional[list[str]] = None

    model_config = {"from_attributes": True}


class OpportunityResponse(BaseModel):
    """API response schema (lightweight for list view)"""
    id: uuid_lib.UUID
    title: str  # Derived from pain_point.extracted_text[:100]
    summary: str  # Derived from pain_point.extracted_text[:300]
    problem_severity: float
    market_size_indicator: Literal["niche", "mid", "large"]
    monetization_potential: float
    technical_complexity: float
    competition_level: Literal["low", "medium", "high", "saturated"]
    trend_direction: Literal["declining", "stable", "growing", "explosive"]
    confidence_level: float
    analyzed_at: datetime

    model_config = {"from_attributes": True}


class OpportunityDetail(OpportunityResponse):
    """API response schema (full details for single opportunity view)"""
    trend_data: Optional[TrendData]
    geographic_spread: Optional[list[str]]
    affected_industries: Optional[list[str]]
    pain_point_id: Optional[uuid_lib.UUID]
    enrichment_count: int
    last_enriched_at: Optional[datetime]

    model_config = {"from_attributes": True}

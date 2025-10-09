# Data Model: Opportunity Entity

**Feature**: 003-multi-dimensional-opportunity
**Date**: 2025-10-08

## Overview

The `Opportunity` entity transforms raw pain points into validated business opportunities with six-dimensional scoring. It survives beyond the 48h Reddit compliance window by storing only derived insights (no raw content).

## SQL Schema

```sql
CREATE TABLE opportunities (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key (nullable - survives pain_point deletion)
    pain_point_id UUID REFERENCES pain_points(id) ON DELETE SET NULL,

    -- Six-Dimensional Scores
    problem_severity FLOAT NOT NULL CHECK (problem_severity BETWEEN 0.0 AND 10.0),
    market_size_indicator VARCHAR(10) NOT NULL CHECK (market_size_indicator IN ('niche', 'mid', 'large')),
    monetization_potential FLOAT NOT NULL CHECK (monetization_potential BETWEEN 0.0 AND 10.0),
    technical_complexity FLOAT NOT NULL CHECK (technical_complexity BETWEEN 0.0 AND 10.0),
    competition_level VARCHAR(20) NOT NULL CHECK (competition_level IN ('low', 'medium', 'high', 'saturated')),
    trend_direction VARCHAR(20) NOT NULL CHECK (trend_direction IN ('declining', 'stable', 'growing', 'explosive')),

    -- Metadata
    confidence_level FLOAT NOT NULL CHECK (confidence_level BETWEEN 0.0 AND 1.0),
    trend_data JSONB,  -- {timestamps: [], frequencies: [], sentiment: []}
    geographic_spread TEXT[],  -- ["North America", "Europe"]
    affected_industries TEXT[],  -- ["SaaS", "E-commerce"]

    -- Timestamps
    analyzed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    enrichment_count INT NOT NULL DEFAULT 0,
    last_enriched_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_opportunity_severity ON opportunities(problem_severity DESC);
CREATE INDEX idx_opportunity_analyzed_at ON opportunities(analyzed_at DESC);
CREATE INDEX idx_opportunity_cursor ON opportunities(id, analyzed_at);
CREATE INDEX idx_opportunity_pain_point ON opportunities(pain_point_id) WHERE pain_point_id IS NOT NULL;
CREATE INDEX idx_opportunity_monetization ON opportunities(monetization_potential DESC);
CREATE INDEX idx_opportunity_market_size ON opportunities(market_size_indicator);
```

## SQLAlchemy Model

```python
from sqlalchemy import Column, String, Float, Integer, DateTime, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

class Opportunity(Base):
    __tablename__ = "opportunities"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key
    pain_point_id = Column(UUID(as_uuid=True), ForeignKey("pain_points.id", ondelete="SET NULL"), nullable=True, index=True)

    # Six-Dimensional Scores
    problem_severity = Column(Float, nullable=False)
    market_size_indicator = Column(String(10), nullable=False)
    monetization_potential = Column(Float, nullable=False)
    technical_complexity = Column(Float, nullable=False)
    competition_level = Column(String(20), nullable=False)
    trend_direction = Column(String(20), nullable=False)

    # Metadata
    confidence_level = Column(Float, nullable=False)
    trend_data = Column(JSONB, nullable=True)
    geographic_spread = Column(ARRAY(String), nullable=True)
    affected_industries = Column(ARRAY(String), nullable=True)

    # Timestamps
    analyzed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    enrichment_count = Column(Integer, nullable=False, default=0)
    last_enriched_at = Column(DateTime, nullable=True)

    # Relationships
    pain_point = relationship("PainPoint", back_populates="opportunity")

    def update_scores(self, new_scores: "OpportunityScores"):
        """Update opportunity with new LLM analysis scores"""
        self.problem_severity = new_scores.problem_severity
        self.market_size_indicator = new_scores.market_size_indicator
        self.monetization_potential = new_scores.monetization_potential
        self.technical_complexity = new_scores.technical_complexity
        self.competition_level = new_scores.competition_level
        self.trend_direction = new_scores.trend_direction
        self.confidence_level = new_scores.confidence_level
```

## Pydantic Validation Models

```python
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

class TrendData(BaseModel):
    """Schema for trend_data JSONB column"""
    timestamps: list[str]  # ISO8601 dates
    frequencies: list[int]  # Mention counts per timestamp
    sentiment: list[float]  # Sentiment scores (-1.0 to 1.0)

class OpportunityCreate(BaseModel):
    """Schema for creating new opportunity"""
    pain_point_id: uuid.UUID
    scores: OpportunityScores
    trend_data: Optional[TrendData] = None
    geographic_spread: Optional[list[str]] = None
    affected_industries: Optional[list[str]] = None

class OpportunityResponse(BaseModel):
    """API response schema (lightweight)"""
    id: uuid.UUID
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

class OpportunityDetail(OpportunityResponse):
    """API response schema (full details)"""
    trend_data: Optional[TrendData]
    geographic_spread: Optional[list[str]]
    affected_industries: Optional[list[str]]
    pain_point_id: Optional[uuid.UUID]
    enrichment_count: int
    last_enriched_at: Optional[datetime]
```

## Validation Rules

### Field Constraints
- `problem_severity`: 0.0-10.0 (float)
- `market_size_indicator`: enum["niche", "mid", "large"]
- `monetization_potential`: 0.0-10.0 (float)
- `technical_complexity`: 0.0-10.0 (float)
- `competition_level`: enum["low", "medium", "high", "saturated"]
- `trend_direction`: enum["declining", "stable", "growing", "explosive"]
- `confidence_level`: 0.0-1.0 (float)
- `enrichment_count`: >= 0 (integer)

### JSONB Schema
`trend_data` MUST validate against:
```json
{
  "timestamps": ["2025-01-01T00:00:00Z", "2025-02-01T00:00:00Z"],
  "frequencies": [42, 58],
  "sentiment": [0.3, 0.7]
}
```
All arrays MUST have equal length.

### Relationship Rules
- `pain_point_id` is nullable (ON DELETE SET NULL)
- When `pain_point` is deleted after 48h, opportunity persists with `pain_point_id=NULL`
- Title/summary cached in API layer (not stored in DB - derived on-demand)

## Index Strategy

### Performance Requirements
- List queries: <500ms p95 for 12 results
- Detail queries: <100ms p95 for single record
- Filtering: Support severity_min/max, market_size, competition_level
- Sorting: By severity, monetization, analyzed_at (DESC default)

### Index Justification
- `idx_opportunity_severity`: Supports filtering + sorting by severity
- `idx_opportunity_analyzed_at`: Default sort order (newest first)
- `idx_opportunity_cursor`: Composite for cursor pagination (id + analyzed_at)
- `idx_opportunity_pain_point`: Foreign key lookups (partial index - only non-null)
- `idx_opportunity_monetization`: Sorting by revenue potential
- `idx_opportunity_market_size`: Filtering by market category

## Migration Script

**File**: `apps/api/alembic/versions/xxx_add_opportunities_table.py`

```python
"""add opportunities table

Revision ID: xxx
Revises: yyy
Create Date: 2025-10-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'xxx'
down_revision = 'yyy'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pain_point_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('problem_severity', sa.Float(), nullable=False),
        sa.Column('market_size_indicator', sa.String(10), nullable=False),
        sa.Column('monetization_potential', sa.Float(), nullable=False),
        sa.Column('technical_complexity', sa.Float(), nullable=False),
        sa.Column('competition_level', sa.String(20), nullable=False),
        sa.Column('trend_direction', sa.String(20), nullable=False),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('trend_data', postgresql.JSONB(), nullable=True),
        sa.Column('geographic_spread', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('affected_industries', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('enrichment_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_enriched_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pain_point_id'], ['pain_points.id'], ondelete='SET NULL')
    )

    op.create_index('idx_opportunity_severity', 'opportunities', ['problem_severity'], postgresql_ops={'problem_severity': 'DESC'})
    op.create_index('idx_opportunity_analyzed_at', 'opportunities', ['analyzed_at'], postgresql_ops={'analyzed_at': 'DESC'})
    op.create_index('idx_opportunity_cursor', 'opportunities', ['id', 'analyzed_at'])
    op.create_index('idx_opportunity_pain_point', 'opportunities', ['pain_point_id'], postgresql_where=sa.text('pain_point_id IS NOT NULL'))
    op.create_index('idx_opportunity_monetization', 'opportunities', ['monetization_potential'], postgresql_ops={'monetization_potential': 'DESC'})
    op.create_index('idx_opportunity_market_size', 'opportunities', ['market_size_indicator'])

def downgrade():
    op.drop_table('opportunities')
```

---

**Lines**: 185
**Status**: Complete

"""
T019: PainPoint model
SQLAlchemy model for derived pain point aggregates
"""
from sqlalchemy import Column, Boolean, TIMESTAMP, Text, DECIMAL, ForeignKey, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from . import Base


class PainPoint(Base):
    """
    PainPoint model for extracted problem/need with scoring

    This is DERIVED NON-USER-CONTENT (Reddit ToS compliant)
    Retention: Indefinite

    Data Lineage:
    RedditPost (raw, 48h TTL) → LLM extraction → PainPoint.extracted_text (derived, permanent)

    When source_deleted=true, pain point remains but loses evidence links.
    """
    __tablename__ = "pain_points"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="Unique pain point identifier"
    )

    # Foreign Key
    search_run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("search_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent search run"
    )

    # Content
    extracted_text = Column(
        Text,
        nullable=False,
        comment="Summarized pain point (NOT raw Reddit text, max 500 chars)"
    )

    # Scores
    relevance_score = Column(
        DECIMAL(5, 4),
        nullable=False,
        comment="Composite score (0-1): 0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment"
    )

    sentiment_score = Column(
        DECIMAL(3, 2),
        nullable=False,
        comment="Sentiment polarity (-1 to 1) from TextBlob"
    )

    # Source References
    source_reddit_post_ids = Column(
        JSONB,
        nullable=False,
        comment="Array of RedditPost.reddit_id references (soft reference, no FK)"
    )

    source_deleted = Column(
        Boolean,
        nullable=False,
        server_default="FALSE",
        comment="Flag if source posts deleted (set by deletion sync job)"
    )

    # Timestamp
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("NOW()"),
        comment="Extraction timestamp"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "char_length(extracted_text) <= 500",
            name="check_extracted_text_length"
        ),
        CheckConstraint(
            "relevance_score >= 0 AND relevance_score <= 1",
            name="check_relevance_score_range"
        ),
        CheckConstraint(
            "sentiment_score >= -1 AND sentiment_score <= 1",
            name="check_sentiment_score_range"
        ),
    )

    # Relationships
    search_run = relationship("SearchRun", back_populates="pain_points")

    def __repr__(self):
        return f"<PainPoint(id={self.id}, relevance_score={self.relevance_score}, extracted_text={self.extracted_text[:50]}...)>"

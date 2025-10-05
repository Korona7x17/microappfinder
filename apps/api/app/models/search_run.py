"""
T017 & T020: SearchRun model and SearchRunTopics join table
SQLAlchemy model for user-initiated discovery sessions
"""
from sqlalchemy import Column, String, Integer, TIMESTAMP, Text, Table, ForeignKey, CheckConstraint
from sqlalchemy.sql import text as sql_text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from . import Base


# T020: SearchRunTopics join table (M:N relationship)
search_run_topics = Table(
    "search_run_topics",
    Base.metadata,
    Column(
        "search_run_id",
        UUID(as_uuid=True),
        ForeignKey("search_runs.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),
    Column(
        "topic_id",
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),
    Column(
        "created_at",
        TIMESTAMP,
        nullable=False,
        server_default=sql_text("NOW()"),
        comment="Assignment timestamp"
    )
)


class SearchRun(Base):
    """
    SearchRun model for Reddit pain point discovery sessions

    State transitions: pending → in_progress → completed/failed
    Retention: Indefinite (linked to user account)
    """
    __tablename__ = "search_runs"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sql_text("gen_random_uuid()"),
        comment="Unique run identifier"
    )

    # Foreign Key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner of search run"
    )

    # Status
    status = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Current state: pending, in_progress, completed, failed"
    )

    # Search Parameters
    time_range = Column(
        String(20),
        nullable=False,
        comment="Time window: 24h, 7days, 30days, 90days, 1year, all"
    )

    # Source Tracking (Feature 002: Multi-source support)
    sources_queried = Column(
        JSONB,
        nullable=False,
        server_default='["reddit"]',
        comment="Array of source platforms queried: reddit, hackernews, etc."
    )

    hn_items_fetched = Column(
        Integer,
        nullable=True,
        comment="Count of HackerNews items fetched (null if HN not queried)"
    )

    # Timestamps
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=sql_text("NOW()"),
        comment="Run creation time"
    )

    started_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="Processing start time"
    )

    completed_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="Processing completion time"
    )

    # Metadata
    pain_points_count = Column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Total pain points extracted"
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Failure reason (if status=failed)"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'failed')",
            name="check_status"
        ),
        CheckConstraint(
            "time_range IN ('24h', '7days', '30days', '90days', '1year', 'all')",
            name="check_time_range"
        ),
        CheckConstraint(
            "hn_items_fetched >= 0 OR hn_items_fetched IS NULL",
            name="check_hn_items_positive"
        ),
    )

    # Relationships
    user = relationship("User", back_populates="search_runs")

    topics = relationship(
        "Topic",
        secondary=search_run_topics,
        back_populates="search_runs"
    )

    pain_points = relationship(
        "PainPoint",
        back_populates="search_run",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<SearchRun(id={self.id}, status={self.status}, user_id={self.user_id})>"

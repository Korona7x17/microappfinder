"""
T011: HackerNewsItem model
SQLAlchemy model for 48h cached HackerNews content
"""
from sqlalchemy import Column, String, Integer, TIMESTAMP, Text, CheckConstraint
from sqlalchemy.sql import text as sql_text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from . import Base


class HackerNewsItem(Base):
    """
    HackerNewsItem model for cached HackerNews content

    48-hour cache pattern (mirrors RedditPost retention)
    Retention: 48h TTL via expires_at

    Cache flow:
    Algolia HN API → HackerNewsItem (48h cache) → PainPoint extraction → Cleanup
    """
    __tablename__ = "hackernews_items"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sql_text("gen_random_uuid()"),
        comment="Unique cache entry identifier"
    )

    # HackerNews Identifiers
    hn_id = Column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="HackerNews item ID (e.g., '12345678')"
    )

    hn_type = Column(
        String(20),
        nullable=False,
        comment="Item type: story, comment, ask_hn, show_hn"
    )

    # Author
    author = Column(
        String(50),
        nullable=True,
        comment="HackerNews username (nullable for deleted accounts)"
    )

    # Content
    title = Column(
        Text,
        nullable=False,
        comment="Story/comment title"
    )

    text = Column(
        Text,
        nullable=True,
        comment="Story text or comment body (nullable for link posts)"
    )

    # URLs
    url = Column(
        String(2048),
        nullable=True,
        comment="External link URL (nullable for text posts)"
    )

    hn_url = Column(
        String(2048),
        nullable=False,
        comment="HackerNews item permalink"
    )

    # Engagement Metrics
    points = Column(
        Integer,
        nullable=False,
        comment="Upvote count (score)"
    )

    comment_count = Column(
        Integer,
        nullable=False,
        comment="Number of comments/descendants"
    )

    # Timestamps
    created_utc = Column(
        TIMESTAMP,
        nullable=False,
        index=True,
        comment="Original HN creation timestamp"
    )

    fetched_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=sql_text("NOW()"),
        comment="Cache insertion timestamp"
    )

    expires_at = Column(
        TIMESTAMP,
        nullable=False,
        index=True,
        comment="Cache expiry timestamp (48h from fetch)"
    )

    # Metadata
    tags = Column(
        JSONB,
        nullable=True,
        comment="Optional metadata: topics, sentiment, extraction flags"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "points >= 0",
            name="check_points_positive"
        ),
        CheckConstraint(
            "comment_count >= 0",
            name="check_comments_positive"
        ),
    )

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired (TTL elapsed)"""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<HackerNewsItem(hn_id={self.hn_id}, title={self.title[:50]}..., points={self.points})>"

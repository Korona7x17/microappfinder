"""
SQLAlchemy models for Reddit Pain Point Discovery
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Legacy models
from app.models.run import Run
from app.models.signal import Signal
from app.models.cluster import Cluster
from app.models.brief import Brief

# Reddit Pain Point Discovery models (Feature 001)
from .user import User
from .topic import Topic
from .search_run import SearchRun, search_run_topics
from .reddit_post import RedditPost
from .pain_point import PainPoint

__all__ = [
    "Base",
    # Legacy
    "Run",
    "Signal",
    "Cluster",
    "Brief",
    # Feature 001
    "User",
    "Topic",
    "SearchRun",
    "search_run_topics",
    "RedditPost",
    "PainPoint",
]

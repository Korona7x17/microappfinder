"""
T009: Opportunity Service
Query logic for opportunities with filtering, sorting, and cursor pagination
"""
import base64
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime

from app.models import Opportunity


class OpportunityService:
    """Service for querying opportunities with filtering and pagination"""

    def __init__(self, db: Session):
        self.db = db

    def list_opportunities(
        self,
        severity_min: Optional[float] = None,
        severity_max: Optional[float] = None,
        market_size: Optional[str] = None,
        competition_level: Optional[str] = None,
        trend_direction: Optional[str] = None,
        sort_by: str = "analyzed_at",
        sort_order: str = "desc",
        cursor: Optional[str] = None,
        limit: int = 12
    ) -> Dict[str, Any]:
        """
        Query opportunities with filtering, sorting, and cursor pagination

        Args:
            severity_min: Minimum problem severity (0-10)
            severity_max: Maximum problem severity (0-10)
            market_size: Filter by market size ('niche', 'mid', 'large')
            competition_level: Filter by competition ('low', 'medium', 'high', 'saturated')
            trend_direction: Filter by trend ('declining', 'stable', 'growing', 'explosive')
            sort_by: Sort field ('severity', 'monetization', 'analyzed_at')
            sort_order: Sort direction ('asc', 'desc')
            cursor: Base64-encoded cursor for pagination
            limit: Number of results (1-50, default 12)

        Returns:
            Dict with opportunities list, next_cursor, and has_more flag
        """
        # Build base query
        query = self.db.query(Opportunity)

        # Apply filters
        if severity_min is not None:
            query = query.filter(Opportunity.problem_severity >= severity_min)
        if severity_max is not None:
            query = query.filter(Opportunity.problem_severity <= severity_max)
        if market_size:
            query = query.filter(Opportunity.market_size_indicator == market_size)
        if competition_level:
            query = query.filter(Opportunity.competition_level == competition_level)
        if trend_direction:
            query = query.filter(Opportunity.trend_direction == trend_direction)

        # Decode cursor if provided
        cursor_data = None
        if cursor:
            try:
                cursor_json = base64.b64decode(cursor).decode('utf-8')
                cursor_data = json.loads(cursor_json)
            except Exception:
                cursor_data = None

        # Apply cursor pagination
        if cursor_data:
            cursor_id = cursor_data.get('id')
            cursor_value = cursor_data.get('value')

            if sort_by == 'severity':
                if sort_order == 'desc':
                    query = query.filter(
                        (Opportunity.problem_severity < cursor_value) |
                        ((Opportunity.problem_severity == cursor_value) & (Opportunity.id < cursor_id))
                    )
                else:
                    query = query.filter(
                        (Opportunity.problem_severity > cursor_value) |
                        ((Opportunity.problem_severity == cursor_value) & (Opportunity.id > cursor_id))
                    )
            elif sort_by == 'monetization':
                if sort_order == 'desc':
                    query = query.filter(
                        (Opportunity.monetization_potential < cursor_value) |
                        ((Opportunity.monetization_potential == cursor_value) & (Opportunity.id < cursor_id))
                    )
                else:
                    query = query.filter(
                        (Opportunity.monetization_potential > cursor_value) |
                        ((Opportunity.monetization_potential == cursor_value) & (Opportunity.id > cursor_id))
                    )
            else:  # analyzed_at
                if sort_order == 'desc':
                    query = query.filter(
                        (Opportunity.analyzed_at < cursor_value) |
                        ((Opportunity.analyzed_at == cursor_value) & (Opportunity.id < cursor_id))
                    )
                else:
                    query = query.filter(
                        (Opportunity.analyzed_at > cursor_value) |
                        ((Opportunity.analyzed_at == cursor_value) & (Opportunity.id > cursor_id))
                    )

        # Apply sorting
        sort_field_map = {
            'severity': Opportunity.problem_severity,
            'monetization': Opportunity.monetization_potential,
            'analyzed_at': Opportunity.analyzed_at
        }
        sort_field = sort_field_map.get(sort_by, Opportunity.analyzed_at)

        if sort_order == 'desc':
            query = query.order_by(desc(sort_field), desc(Opportunity.id))
        else:
            query = query.order_by(asc(sort_field), asc(Opportunity.id))

        # Fetch limit + 1 to check for more results
        opportunities = query.limit(limit + 1).all()

        # Check if there are more results
        has_more = len(opportunities) > limit
        if has_more:
            opportunities = opportunities[:limit]

        # Generate next cursor
        next_cursor = None
        if has_more and opportunities:
            last_opp = opportunities[-1]
            cursor_value = getattr(last_opp, sort_field.name)
            if isinstance(cursor_value, datetime):
                cursor_value = cursor_value.isoformat()

            cursor_dict = {
                'id': str(last_opp.id),
                'value': cursor_value
            }
            cursor_json = json.dumps(cursor_dict)
            next_cursor = base64.b64encode(cursor_json.encode('utf-8')).decode('utf-8')

        return {
            'opportunities': opportunities,
            'next_cursor': next_cursor,
            'has_more': has_more
        }

    def get_opportunity_by_id(self, opportunity_id: str) -> Optional[Opportunity]:
        """
        Get a single opportunity by ID

        Args:
            opportunity_id: UUID of the opportunity

        Returns:
            Opportunity or None if not found
        """
        return self.db.query(Opportunity).filter(
            Opportunity.id == opportunity_id
        ).first()

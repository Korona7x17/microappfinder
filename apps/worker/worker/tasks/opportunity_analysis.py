"""
T007: Opportunity Analysis Worker Task
Analyzes top pain points and creates Opportunity records with LLM-generated scores
"""
import logging
import time
from uuid import UUID
from typing import List, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import SessionLocal
from app.models import PainPoint, Opportunity
from app.services.opportunity_analysis_service import OpportunityAnalysisService

logger = logging.getLogger(__name__)


def analyze_top_pain_points(search_run_id: UUID, pain_point_ids: List[UUID]) -> Dict:
    """
    Analyze top pain points and create Opportunity records

    Args:
        search_run_id: UUID of the search run (for logging context)
        pain_point_ids: List of pain point UUIDs to analyze (1-10 items per contract)

    Returns:
        Dict with metrics:
        - opportunities_created: Number of opportunities successfully created
        - analysis_duration_ms: Total analysis time in milliseconds
        - coverage_rate: Ratio of successful analyses (0.0-1.0)

    Raises:
        ValueError: If pain_point_ids is empty or exceeds 10 items
        AssertionError: If pain_point_ids violates contract constraints
    """
    # Validate contract constraints
    if len(pain_point_ids) < 1:
        raise ValueError("pain_point_ids must contain at least 1 element (contract: min_length=1)")
    if len(pain_point_ids) > 10:
        raise ValueError("pain_point_ids must contain at most 10 elements (contract: max_length=10)")

    logger.info(
        f"Starting opportunity analysis for search_run {search_run_id}: "
        f"{len(pain_point_ids)} pain points to analyze"
    )

    start_time = time.time()

    # Initialize service
    analysis_service = OpportunityAnalysisService()

    # Track metrics
    opportunities_created = 0
    successful_analyses = 0

    # Get database session
    session: Session = SessionLocal()

    try:
        for pain_point_id in pain_point_ids:
            try:
                # Fetch pain point
                pain_point = session.query(PainPoint).filter(
                    PainPoint.id == pain_point_id
                ).first()

                if not pain_point:
                    logger.warning(
                        f"Pain point {pain_point_id} not found, skipping",
                        extra={"search_run_id": str(search_run_id)}
                    )
                    continue

                logger.info(
                    f"Analyzing pain point {pain_point_id} from {pain_point.source_platform}",
                    extra={"search_run_id": str(search_run_id)}
                )

                # Analyze pain point with LLM
                scores = analysis_service.analyze_pain_point(pain_point)

                if scores is None:
                    logger.warning(
                        f"Analysis failed for pain point {pain_point_id}, skipping",
                        extra={"search_run_id": str(search_run_id)}
                    )
                    continue

                successful_analyses += 1

                # Create Opportunity record
                opportunity = Opportunity(
                    title=_generate_title(pain_point.extracted_text, scores),
                    summary=pain_point.extracted_text[:500],  # First 500 chars
                    problem_severity=scores.problem_severity,
                    market_size_indicator=scores.market_size_indicator,
                    monetization_potential=scores.monetization_potential,
                    technical_complexity=scores.technical_complexity,
                    competition_level=scores.competition_level,
                    trend_direction=scores.trend_direction,
                    confidence_level=scores.confidence_level,
                    analyzed_at=datetime.utcnow(),
                    pain_point_id=pain_point_id,
                    enrichment_count=0,
                    # Optional fields remain None for now
                    trend_data=None,
                    geographic_spread=None,
                    affected_industries=None,
                    last_enriched_at=None
                )

                session.add(opportunity)
                session.commit()

                opportunities_created += 1

                logger.info(
                    f"Created opportunity for pain point {pain_point_id}: "
                    f"severity={scores.problem_severity:.1f}, "
                    f"monetization={scores.monetization_potential:.1f}",
                    extra={"search_run_id": str(search_run_id)}
                )

            except Exception as e:
                logger.error(
                    f"Failed to analyze pain point {pain_point_id}: {e}",
                    exc_info=True,
                    extra={"search_run_id": str(search_run_id)}
                )
                session.rollback()
                # Continue processing other pain points
                continue

    finally:
        session.close()

    # Calculate final metrics
    end_time = time.time()
    duration_ms = int((end_time - start_time) * 1000)
    coverage_rate = successful_analyses / len(pain_point_ids) if pain_point_ids else 0.0

    logger.info(
        f"Opportunity analysis complete for search_run {search_run_id}: "
        f"{opportunities_created} opportunities created, "
        f"{duration_ms}ms duration, "
        f"{coverage_rate:.2%} coverage rate",
        extra={"search_run_id": str(search_run_id)}
    )

    return {
        "opportunities_created": opportunities_created,
        "analysis_duration_ms": duration_ms,
        "coverage_rate": coverage_rate
    }


def _generate_title(extracted_text: str, scores) -> str:
    """
    Generate a concise opportunity title from pain point text

    Args:
        extracted_text: Original pain point text
        scores: OpportunityScores with analysis results

    Returns:
        Title string (max 100 chars)
    """
    # Extract first sentence or first 80 chars
    text = extracted_text.strip()

    # Try to get first sentence
    for delimiter in ['. ', '! ', '? ']:
        if delimiter in text:
            first_sentence = text.split(delimiter)[0] + '.'
            if len(first_sentence) <= 100:
                return first_sentence
            break

    # Fallback: truncate to 100 chars
    if len(text) > 97:
        return text[:97] + '...'

    return text

"""
T012: Integration test for end-to-end opportunity workflow
Tests the complete flow: Pain Point → LLM Analysis → Opportunity Creation
"""
import pytest
from sqlalchemy.orm import Session
import uuid as uuid_lib
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.models import PainPoint, Opportunity
from app.services.llm_analysis_service import LLMAnalysisService
from app.models.opportunity import OpportunityScores


class TestOpportunityWorkflowIntegration:
    """Integration tests for complete opportunity creation workflow"""

    @pytest.fixture
    def sample_pain_points(self, db_session: Session):
        """Create sample pain points for testing"""
        pain_points = []

        # Pain point 1: High severity problem
        pp1 = PainPoint(
            id=str(uuid_lib.uuid4()),
            search_run_id=str(uuid_lib.uuid4()),
            extracted_text="I'm spending 3+ hours daily manually exporting data from multiple sources. "
                          "No existing tools support batch export with custom formatting. "
                          "This is critical for our reporting workflow.",
            relevance_score=0.95,
            sentiment_score=-0.8,
            source_platform="reddit",
            source_post_ids=["t3_abc123"],
            source_deleted=False,
            created_at=datetime.utcnow()
        )
        pain_points.append(pp1)

        # Pain point 2: Medium severity with monetization potential
        pp2 = PainPoint(
            id=str(uuid_lib.uuid4()),
            search_run_id=str(uuid_lib.uuid4()),
            extracted_text="Need a simple way to track SaaS subscriptions and get alerts before renewal. "
                          "Tried 3 different apps but they're all either too complex or don't support alerts.",
            relevance_score=0.85,
            sentiment_score=-0.6,
            source_platform="hackernews",
            source_post_ids=["hn_123456"],
            source_deleted=False,
            created_at=datetime.utcnow()
        )
        pain_points.append(pp2)

        # Pain point 3: Low severity, niche problem
        pp3 = PainPoint(
            id=str(uuid_lib.uuid4()),
            search_run_id=str(uuid_lib.uuid4()),
            extracted_text="Looking for a tool to organize my Pokemon card collection. "
                          "Nothing exists specifically for this hobby.",
            relevance_score=0.65,
            sentiment_score=-0.3,
            source_platform="reddit",
            source_post_ids=["t3_xyz789"],
            source_deleted=False,
            created_at=datetime.utcnow()
        )
        pain_points.append(pp3)

        for pp in pain_points:
            db_session.add(pp)
        db_session.commit()

        return pain_points

    @pytest.fixture
    def mock_llm_analysis(self):
        """Mock LLM analysis responses for different scenarios"""
        def analysis_side_effect(pain_point_text: str) -> OpportunityScores:
            # High severity data export problem
            if "3+ hours daily" in pain_point_text:
                return OpportunityScores(
                    problem_severity=9.5,
                    market_size_indicator="large",
                    monetization_potential=8.5,
                    technical_complexity=6.0,
                    competition_level="medium",
                    trend_direction="growing",
                    confidence_level=0.92,
                    reasoning="Critical business workflow bottleneck with clear monetization path. "
                             "Medium technical complexity but growing market demand."
                )
            # Medium severity subscription tracking
            elif "SaaS subscriptions" in pain_point_text:
                return OpportunityScores(
                    problem_severity=7.0,
                    market_size_indicator="mid",
                    monetization_potential=7.5,
                    technical_complexity=4.0,
                    competition_level="high",
                    trend_direction="stable",
                    confidence_level=0.85,
                    reasoning="Common problem with existing solutions. Differentiation possible through simplicity."
                )
            # Low severity niche problem
            else:
                return OpportunityScores(
                    problem_severity=3.5,
                    market_size_indicator="niche",
                    monetization_potential=4.0,
                    technical_complexity=3.0,
                    competition_level="low",
                    trend_direction="stable",
                    confidence_level=0.70,
                    reasoning="Niche hobby problem with limited market size but low competition."
                )

        return analysis_side_effect

    def test_end_to_end_opportunity_creation(
        self,
        db_session: Session,
        sample_pain_points,
        mock_llm_analysis
    ):
        """Test complete workflow from pain point to opportunity"""
        # Mock the LLM service
        with patch.object(LLMAnalysisService, 'analyze_opportunity') as mock_analyze:
            mock_analyze.side_effect = mock_llm_analysis

            service = LLMAnalysisService()
            created_opportunities = []

            # Process each pain point through LLM analysis
            for pain_point in sample_pain_points:
                # Analyze pain point
                scores = service.analyze_opportunity(pain_point.extracted_text)

                # Create opportunity
                opportunity = Opportunity(
                    pain_point_id=pain_point.id,
                    title=pain_point.extracted_text[:100],
                    summary=pain_point.extracted_text[:500],
                    problem_severity=scores.problem_severity,
                    market_size_indicator=scores.market_size_indicator,
                    monetization_potential=scores.monetization_potential,
                    technical_complexity=scores.technical_complexity,
                    competition_level=scores.competition_level,
                    trend_direction=scores.trend_direction,
                    confidence_level=scores.confidence_level,
                    analyzed_at=datetime.utcnow(),
                    enrichment_count=0
                )

                db_session.add(opportunity)
                created_opportunities.append(opportunity)

            db_session.commit()

            # Verify all opportunities were created
            assert len(created_opportunities) == 3

            # Verify high severity opportunity
            high_sev_opp = created_opportunities[0]
            assert high_sev_opp.problem_severity == 9.5
            assert high_sev_opp.market_size_indicator == "large"
            assert high_sev_opp.monetization_potential == 8.5
            assert high_sev_opp.competition_level == "medium"
            assert high_sev_opp.trend_direction == "growing"
            assert high_sev_opp.confidence_level == 0.92

            # Verify medium severity opportunity
            mid_sev_opp = created_opportunities[1]
            assert mid_sev_opp.problem_severity == 7.0
            assert mid_sev_opp.market_size_indicator == "mid"
            assert mid_sev_opp.competition_level == "high"

            # Verify low severity opportunity
            low_sev_opp = created_opportunities[2]
            assert low_sev_opp.problem_severity == 3.5
            assert low_sev_opp.market_size_indicator == "niche"
            assert low_sev_opp.competition_level == "low"

    def test_opportunity_persists_after_pain_point_deletion(
        self,
        db_session: Session,
        sample_pain_points,
        mock_llm_analysis
    ):
        """Test opportunity survives pain point deletion (Reddit 48h TTL compliance)"""
        pain_point = sample_pain_points[0]

        # Mock LLM and create opportunity
        with patch.object(LLMAnalysisService, 'analyze_opportunity') as mock_analyze:
            mock_analyze.side_effect = mock_llm_analysis

            service = LLMAnalysisService()
            scores = service.analyze_opportunity(pain_point.extracted_text)

            opportunity = Opportunity(
                pain_point_id=pain_point.id,
                title=pain_point.extracted_text[:100],
                summary=pain_point.extracted_text[:500],
                problem_severity=scores.problem_severity,
                market_size_indicator=scores.market_size_indicator,
                monetization_potential=scores.monetization_potential,
                technical_complexity=scores.technical_complexity,
                competition_level=scores.competition_level,
                trend_direction=scores.trend_direction,
                confidence_level=scores.confidence_level,
                analyzed_at=datetime.utcnow(),
                enrichment_count=0
            )

            db_session.add(opportunity)
            db_session.commit()

            opportunity_id = opportunity.id

            # Verify opportunity has pain_point_id
            assert opportunity.pain_point_id == pain_point.id

            # Delete pain point (simulates 48h TTL expiration)
            db_session.delete(pain_point)
            db_session.commit()

            # Refresh opportunity from database
            persisted_opp = db_session.query(Opportunity).filter_by(id=opportunity_id).first()

            # Verify opportunity still exists
            assert persisted_opp is not None
            # Verify pain_point_id is now NULL (due to ondelete="SET NULL")
            assert persisted_opp.pain_point_id is None
            # Verify all opportunity data persists
            assert persisted_opp.problem_severity == scores.problem_severity
            assert persisted_opp.title == pain_point.extracted_text[:100]
            assert persisted_opp.summary == pain_point.extracted_text[:500]

    def test_opportunity_score_validation(
        self,
        db_session: Session,
        sample_pain_points,
        mock_llm_analysis
    ):
        """Test that opportunity scores are properly validated"""
        pain_point = sample_pain_points[0]

        with patch.object(LLMAnalysisService, 'analyze_opportunity') as mock_analyze:
            mock_analyze.side_effect = mock_llm_analysis

            service = LLMAnalysisService()
            scores = service.analyze_opportunity(pain_point.extracted_text)

            # Verify score ranges
            assert 0.0 <= scores.problem_severity <= 10.0
            assert scores.market_size_indicator in ["niche", "mid", "large"]
            assert 0.0 <= scores.monetization_potential <= 10.0
            assert 0.0 <= scores.technical_complexity <= 10.0
            assert scores.competition_level in ["low", "medium", "high", "saturated"]
            assert scores.trend_direction in ["declining", "stable", "growing", "explosive"]
            assert 0.0 <= scores.confidence_level <= 1.0

    def test_batch_opportunity_creation_performance(
        self,
        db_session: Session,
        mock_llm_analysis
    ):
        """Test bulk opportunity creation for performance validation"""
        # Create 10 pain points
        pain_points = []
        for i in range(10):
            pp = PainPoint(
                id=str(uuid_lib.uuid4()),
                search_run_id=str(uuid_lib.uuid4()),
                extracted_text=f"Pain point {i}: Need better tools for task automation",
                relevance_score=0.8,
                sentiment_score=-0.5,
                source_platform="reddit",
                source_post_ids=[f"t3_test{i}"],
                source_deleted=False,
                created_at=datetime.utcnow()
            )
            pain_points.append(pp)
            db_session.add(pp)

        db_session.commit()

        # Batch process
        with patch.object(LLMAnalysisService, 'analyze_opportunity') as mock_analyze:
            mock_analyze.side_effect = mock_llm_analysis

            service = LLMAnalysisService()
            opportunities = []

            for pain_point in pain_points:
                scores = service.analyze_opportunity(pain_point.extracted_text)

                opportunity = Opportunity(
                    pain_point_id=pain_point.id,
                    title=pain_point.extracted_text[:100],
                    summary=pain_point.extracted_text[:500],
                    problem_severity=scores.problem_severity,
                    market_size_indicator=scores.market_size_indicator,
                    monetization_potential=scores.monetization_potential,
                    technical_complexity=scores.technical_complexity,
                    competition_level=scores.competition_level,
                    trend_direction=scores.trend_direction,
                    confidence_level=scores.confidence_level,
                    analyzed_at=datetime.utcnow(),
                    enrichment_count=0
                )

                opportunities.append(opportunity)
                db_session.add(opportunity)

            db_session.commit()

            # Verify all created
            assert len(opportunities) == 10

            # Verify all persisted
            persisted_count = db_session.query(Opportunity).count()
            assert persisted_count == 10

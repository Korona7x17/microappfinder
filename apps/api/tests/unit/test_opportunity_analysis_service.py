"""
T005: Unit tests for OpportunityAnalysisService
Verifies service initialization and basic functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from decimal import Decimal

from app.services.opportunity_analysis_service import OpportunityAnalysisService
from app.models import PainPoint, OpportunityScores


class TestOpportunityAnalysisService:
    """Unit tests for opportunity analysis service"""

    def test_service_initializes_with_api_keys(self, monkeypatch):
        """Test service initializes OpenAI and Anthropic clients when API keys are set"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

        service = OpportunityAnalysisService()

        assert service.openai_client is not None
        assert service.anthropic_client is not None

    def test_service_initializes_without_api_keys(self, monkeypatch):
        """Test service initializes gracefully when API keys are missing"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        service = OpportunityAnalysisService()

        assert service.openai_client is None
        assert service.anthropic_client is None

    @patch('app.services.opportunity_analysis_service.OpenAI')
    def test_analyze_pain_point_with_openai_success(self, mock_openai_class, monkeypatch):
        """Test successful analysis using GPT-4o-mini"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "problem_severity": 7.5,
            "market_size_indicator": "mid",
            "monetization_potential": 6.0,
            "technical_complexity": 4.5,
            "competition_level": "medium",
            "trend_direction": "growing",
            "confidence_level": 0.75,
            "reasoning": "Clear pain point with moderate market"
        }"""
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 1500
        mock_response.usage.completion_tokens = 300
        mock_response.usage.total_tokens = 1800

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        service = OpportunityAnalysisService()

        # Create mock pain point
        pain_point = Mock(spec=PainPoint)
        pain_point.id = uuid4()
        pain_point.extracted_text = "I struggle to find good tools for project management"
        pain_point.source_platform = "reddit"
        pain_point.relevance_score = Decimal("0.85")

        # Analyze
        result = service.analyze_pain_point(pain_point)

        # Verify result
        assert result is not None
        assert isinstance(result, OpportunityScores)
        assert result.problem_severity == 7.5
        assert result.market_size_indicator == "mid"
        assert result.monetization_potential == 6.0
        assert result.technical_complexity == 4.5
        assert result.competition_level == "medium"
        assert result.trend_direction == "growing"
        assert result.confidence_level == 0.75

    @patch('app.services.opportunity_analysis_service.OpenAI')
    def test_analyze_pain_point_openai_failure_triggers_fallback(self, mock_openai_class, monkeypatch):
        """Test that OpenAI failure triggers Claude fallback"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

        # Mock OpenAI to raise exception
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_openai_client

        service = OpportunityAnalysisService()

        # Mock Claude response
        with patch.object(service, '_fallback_to_claude') as mock_claude:
            mock_claude.return_value = OpportunityScores(
                problem_severity=6.0,
                market_size_indicator="niche",
                monetization_potential=5.0,
                technical_complexity=3.0,
                competition_level="low",
                trend_direction="stable",
                confidence_level=0.6,
                reasoning="Fallback analysis"
            )

            pain_point = Mock(spec=PainPoint)
            pain_point.id = uuid4()
            pain_point.extracted_text = "Test pain point"
            pain_point.source_platform = "reddit"
            pain_point.relevance_score = Decimal("0.75")

            result = service.analyze_pain_point(pain_point)

            # Verify fallback was called
            mock_claude.assert_called_once()
            assert result is not None
            assert result.problem_severity == 6.0

    @patch('app.services.opportunity_analysis_service.OpenAI')
    def test_analyze_pain_point_returns_none_on_invalid_json(self, mock_openai_class, monkeypatch):
        """Test that invalid JSON response is handled gracefully"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        # Mock OpenAI response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not JSON"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        service = OpportunityAnalysisService()

        pain_point = Mock(spec=PainPoint)
        pain_point.id = uuid4()
        pain_point.extracted_text = "Test"
        pain_point.source_platform = "reddit"
        pain_point.relevance_score = Decimal("0.5")

        result = service.analyze_pain_point(pain_point)

        # Should return None when both primary and fallback fail
        assert result is None

    @patch('app.services.opportunity_analysis_service.OpenAI')
    def test_analyze_pain_point_validates_score_ranges(self, mock_openai_class, monkeypatch):
        """Test that Pydantic validates score ranges"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        # Mock OpenAI response with invalid ranges
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "problem_severity": 15.0,
            "market_size_indicator": "mid",
            "monetization_potential": 6.0,
            "technical_complexity": 4.5,
            "competition_level": "medium",
            "trend_direction": "growing",
            "confidence_level": 0.75,
            "reasoning": "Test"
        }"""

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        service = OpportunityAnalysisService()

        pain_point = Mock(spec=PainPoint)
        pain_point.id = uuid4()
        pain_point.extracted_text = "Test"
        pain_point.source_platform = "reddit"
        pain_point.relevance_score = Decimal("0.5")

        result = service.analyze_pain_point(pain_point)

        # Should return None due to validation error
        assert result is None

    def test_build_analysis_prompt_includes_all_dimensions(self, monkeypatch):
        """Test that prompt includes all 6 scoring dimensions"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        service = OpportunityAnalysisService()

        pain_point = Mock(spec=PainPoint)
        pain_point.extracted_text = "I need better tools for data visualization"
        pain_point.source_platform = "hackernews"
        pain_point.relevance_score = Decimal("0.92")

        prompt = service._build_analysis_prompt(pain_point)

        # Verify all required elements are in prompt
        assert "problem_severity" in prompt
        assert "market_size_indicator" in prompt
        assert "monetization_potential" in prompt
        assert "technical_complexity" in prompt
        assert "competition_level" in prompt
        assert "trend_direction" in prompt
        assert "confidence_level" in prompt

        # Verify pain point text is included
        assert "data visualization" in prompt
        assert "hackernews" in prompt
        assert "0.920" in prompt

    def test_build_analysis_prompt_includes_rubrics(self, monkeypatch):
        """Test that prompt includes scoring rubrics for consistency"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        service = OpportunityAnalysisService()

        pain_point = Mock(spec=PainPoint)
        pain_point.extracted_text = "Test"
        pain_point.source_platform = "reddit"
        pain_point.relevance_score = Decimal("0.5")

        prompt = service._build_analysis_prompt(pain_point)

        # Verify rubrics are present
        assert "0-10" in prompt
        assert "niche" in prompt
        assert "mid" in prompt
        assert "large" in prompt
        assert "low" in prompt
        assert "medium" in prompt
        assert "high" in prompt
        assert "saturated" in prompt
        assert "declining" in prompt
        assert "stable" in prompt
        assert "growing" in prompt
        assert "explosive" in prompt

    @patch('app.services.opportunity_analysis_service.Anthropic')
    def test_claude_fallback_strips_markdown(self, mock_anthropic_class, monkeypatch):
        """Test that Claude fallback strips markdown code blocks"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        # Mock Claude response with markdown
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """```json
{
    "problem_severity": 5.0,
    "market_size_indicator": "niche",
    "monetization_potential": 4.0,
    "technical_complexity": 3.0,
    "competition_level": "low",
    "trend_direction": "stable",
    "confidence_level": 0.5,
    "reasoning": "Test"
}
```"""
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 1200
        mock_response.usage.output_tokens = 250

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        service = OpportunityAnalysisService()

        pain_point = Mock(spec=PainPoint)
        pain_point.id = uuid4()
        pain_point.extracted_text = "Test"
        pain_point.source_platform = "reddit"
        pain_point.relevance_score = Decimal("0.5")

        result = service._fallback_to_claude(pain_point)

        # Should successfully parse despite markdown
        assert result is not None
        assert isinstance(result, OpportunityScores)
        assert result.problem_severity == 5.0

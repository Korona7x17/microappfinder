"""
T005: Opportunity Analysis Service
Analyzes individual pain points using GPT-4o-mini with Claude fallback
Returns structured OpportunityScores with 6-dimensional analysis
"""
import os
import json
import logging
from typing import Optional
from openai import OpenAI
from anthropic import Anthropic
from pydantic import ValidationError

from app.models import PainPoint, OpportunityScores

logger = logging.getLogger(__name__)


class OpportunityAnalysisService:
    """
    LLM-powered opportunity analysis service

    Primary: GPT-4o-mini with structured JSON output
    Fallback: Claude Sonnet 3.5 on failure
    Token budget: 2000 input + 500 output = 2500 total
    """

    def __init__(self):
        """Initialize LLM clients with API keys from environment"""
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if not openai_key:
            logger.warning("OPENAI_API_KEY not set - GPT-4o-mini analysis will fail")
        if not anthropic_key:
            logger.warning("ANTHROPIC_API_KEY not set - Claude fallback unavailable")

        self.openai_client = OpenAI(api_key=openai_key) if openai_key else None
        self.anthropic_client = Anthropic(api_key=anthropic_key) if anthropic_key else None

    def analyze_pain_point(self, pain_point: PainPoint) -> Optional[OpportunityScores]:
        """
        Analyze a single pain point to generate opportunity scores

        Args:
            pain_point: PainPoint model with extracted_text, relevance_score, source_platform

        Returns:
            OpportunityScores object with 6-dimensional analysis, or None on failure

        Token budget: ~2000 input (prompt + context) + 500 output = 2500 total
        """
        logger.info(f"Analyzing pain point {pain_point.id} from {pain_point.source_platform}")

        # Try GPT-4o-mini first
        try:
            return self._analyze_with_openai(pain_point)
        except Exception as e:
            logger.error(f"GPT-4o-mini analysis failed for {pain_point.id}: {e}", exc_info=True)

            # Fallback to Claude Sonnet
            return self._fallback_to_claude(pain_point)

    def _analyze_with_openai(self, pain_point: PainPoint) -> Optional[OpportunityScores]:
        """
        Analyze pain point using GPT-4o-mini with structured JSON output

        Args:
            pain_point: Pain point to analyze

        Returns:
            OpportunityScores or None on failure
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        prompt = self._build_analysis_prompt(pain_point)

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing business opportunities. "
                                   "Return analysis as valid JSON matching the provided schema."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Lower temperature for consistent scoring
                max_tokens=500,   # Output token budget
            )

            # Extract JSON from response
            content = response.choices[0].message.content
            data = json.loads(content)

            # Validate and parse with Pydantic
            scores = OpportunityScores(**data)

            # Log token usage for monitoring
            usage = response.usage
            logger.info(
                f"OpenAI analysis complete for {pain_point.id}: "
                f"{usage.prompt_tokens} input + {usage.completion_tokens} output = {usage.total_tokens} tokens"
            )

            return scores

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from GPT-4o-mini: {e}")
            return None
        except ValidationError as e:
            logger.error(f"Validation error from GPT-4o-mini output: {e}")
            return None
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise  # Re-raise to trigger Claude fallback

    def _fallback_to_claude(self, pain_point: PainPoint) -> Optional[OpportunityScores]:
        """
        Fallback to Claude Sonnet 3.5 when GPT-4o-mini fails

        Args:
            pain_point: Pain point to analyze

        Returns:
            OpportunityScores or None on failure
        """
        if not self.anthropic_client:
            logger.error("Claude fallback unavailable - no API key")
            return None

        logger.info(f"Falling back to Claude Sonnet for {pain_point.id}")

        prompt = self._build_analysis_prompt(pain_point)

        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-3-5-20241022",
                max_tokens=500,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt + "\n\nIMPORTANT: Respond with valid JSON only, no markdown formatting."
                    }
                ]
            )

            # Extract JSON from response
            content = response.content[0].text

            # Clean potential markdown formatting
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            # Validate and parse with Pydantic
            scores = OpportunityScores(**data)

            # Log token usage
            usage = response.usage
            logger.info(
                f"Claude analysis complete for {pain_point.id}: "
                f"{usage.input_tokens} input + {usage.output_tokens} output tokens"
            )

            return scores

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from Claude: {e}")
            return None
        except ValidationError as e:
            logger.error(f"Validation error from Claude output: {e}")
            return None
        except Exception as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            return None

    def _build_analysis_prompt(self, pain_point: PainPoint) -> str:
        """
        Build analysis prompt with 6-dimensional rubric

        Args:
            pain_point: Pain point to analyze

        Returns:
            Formatted prompt string
        """
        # Extract context
        text = pain_point.extracted_text
        platform = pain_point.source_platform
        relevance = float(pain_point.relevance_score)

        prompt = f"""Analyze this user pain point for business opportunity potential.

**Pain Point**:
{text}

**Context**:
- Source: {platform}
- Relevance Score: {relevance:.3f} (higher = more upvotes/engagement)

**Task**: Score this opportunity across 6 dimensions and return valid JSON.

**Output JSON Schema**:
```json
{{
  "problem_severity": <float 0-10>,
  "market_size_indicator": "<'niche' | 'mid' | 'large'>",
  "monetization_potential": <float 0-10>,
  "technical_complexity": <float 0-10>,
  "competition_level": "<'low' | 'medium' | 'high' | 'saturated'>",
  "trend_direction": "<'declining' | 'stable' | 'growing' | 'explosive'>",
  "confidence_level": <float 0-1>,
  "reasoning": "<brief explanation for scores>"
}}
```

**Scoring Rubrics**:

1. **Problem Severity** (0-10):
   - 0-3: Minor inconvenience, workarounds exist
   - 4-6: Moderate pain, impacts productivity
   - 7-8: Significant pain, frequent frustration
   - 9-10: Critical blocker, urgent need

2. **Market Size Indicator**:
   - "niche": <10k potential users, specialized domain
   - "mid": 10k-500k potential users, common workflow
   - "large": >500k potential users, universal problem

3. **Monetization Potential** (0-10):
   - 0-3: Unlikely to pay (nice-to-have)
   - 4-6: Moderate willingness (saves time/money)
   - 7-8: High willingness (critical workflow)
   - 9-10: Premium potential (enterprise/mission-critical)

4. **Technical Complexity** (0-10):
   - 0-3: Simple CRUD app, existing libraries
   - 4-6: Moderate complexity, custom logic
   - 7-8: Complex integrations, specialized domain
   - 9-10: Research-level, novel algorithms

5. **Competition Level**:
   - "low": No direct competitors mentioned
   - "medium": 1-2 existing solutions
   - "high": Many competitors, crowded space
   - "saturated": Dominant incumbents, hard to differentiate

6. **Trend Direction**:
   - "declining": Old problem, fading discussion
   - "stable": Consistent mentions, mature space
   - "growing": Increasing discussion, emerging need
   - "explosive": Rapid growth, hot topic

**Confidence Level** (0-1):
- 0.0-0.3: Vague problem, insufficient evidence
- 0.4-0.6: Moderate clarity, some assumptions
- 0.7-0.9: Clear problem, strong evidence
- 1.0: Explicit need, quantified impact

Return ONLY valid JSON matching the schema above."""

        return prompt

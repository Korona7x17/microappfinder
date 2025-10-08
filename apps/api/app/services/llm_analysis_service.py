"""
LLM-powered opportunity analysis service
Two-tier approach: GPT-4o-mini (quick filter) → Claude Sonnet (deep analysis)
"""
from typing import List, Dict, Any, Optional
import os
import json
import logging
from openai import OpenAI
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class LLMAnalysisService:
    """
    Two-tier LLM analysis for opportunity detection

    Tier 1 (GPT-4o-mini):
    - Analyzes top 30 pre-filtered candidates
    - Uses title + 500 chars for quick assessment
    - Selects top 10 most promising opportunities
    - Cost: ~$0.003 per search

    Tier 2 (Claude Sonnet):
    - Deep analyzes top 10 from Tier 1
    - Uses full content (up to 2000 chars)
    - Provides detailed opportunity breakdown
    - Selects final top 5 with insights
    - Cost: ~$0.06 per search

    Total cost per search: ~$0.06
    """

    def __init__(self):
        """Initialize LLM clients"""
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def analyze_opportunities(
        self,
        candidates: List[Dict[str, Any]],
        tier1_limit: int = 10,
        tier2_limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Two-tier analysis pipeline

        Args:
            candidates: Pre-filtered candidates (max ~30)
            tier1_limit: How many to pass to Tier 2 (default 10)
            tier2_limit: Final number of opportunities (default 5)

        Returns:
            Top opportunities with LLM-generated insights
        """
        if not candidates:
            logger.warning("No candidates to analyze")
            return []

        logger.info(f"Starting two-tier analysis on {len(candidates)} candidates")

        # Tier 1: Quick filter with GPT-4o-mini
        tier1_results = self._tier1_quick_filter(candidates, limit=tier1_limit)

        if not tier1_results:
            logger.warning("Tier 1 returned no candidates")
            return []

        # Tier 2: Deep analysis with Claude Sonnet
        tier2_results = self._tier2_deep_analysis(tier1_results, limit=tier2_limit)

        logger.info(f"Analysis complete: {len(tier2_results)} final opportunities")

        return tier2_results

    def _tier1_quick_filter(
        self,
        candidates: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Tier 1: GPT-4o-mini batch analysis

        Analyzes title + 500 chars to quickly identify promising opportunities

        Args:
            candidates: List of candidates
            limit: Number of top candidates to return

        Returns:
            Top candidates from Tier 1 analysis
        """
        logger.info(f"Tier 1: Analyzing {len(candidates)} candidates with GPT-4o-mini")

        # Prepare batch prompt
        batch_content = self._prepare_tier1_batch(candidates)

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at identifying micro SaaS opportunities from online discussions.

Analyze the following threads and identify the TOP opportunities based on:
1. Advice requests - people asking for help or guidance
2. Solution requests - people looking for tools, apps, or ways to solve problems
3. Pain and anger - frustrations and challenges people are facing
4. Problems being discussed - issues that come up frequently
5. Signs of willingness to pay or strong interest
6. Market validation signals - multiple people with similar needs

Return ONLY a JSON array of the top thread IDs in priority order.
Format: ["id1", "id2", "id3", ...]

Be selective - only include truly promising opportunities."""
                    },
                    {
                        "role": "user",
                        "content": batch_content
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )

            # Parse response
            result_text = response.choices[0].message.content.strip()

            # Extract JSON array
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()

            top_ids = json.loads(result_text)

            # Return candidates in priority order
            selected = []
            for thread_id in top_ids[:limit]:
                for candidate in candidates:
                    if candidate.get("id") == thread_id:
                        selected.append(candidate)
                        break

            logger.info(f"Tier 1 selected {len(selected)} candidates")
            return selected

        except Exception as e:
            logger.error(f"Tier 1 analysis failed: {str(e)}")
            # Fallback: return top N by composite score
            return sorted(candidates, key=lambda x: x.get("composite_score", 0), reverse=True)[:limit]

    def _tier2_deep_analysis(
        self,
        candidates: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Tier 2: Claude Sonnet deep analysis

        Provides detailed opportunity assessment with insights

        Args:
            candidates: Top candidates from Tier 1
            limit: Final number of opportunities

        Returns:
            Top opportunities with detailed insights
        """
        logger.info(f"Tier 2: Deep analyzing {len(candidates)} candidates with Claude Sonnet")

        # Prepare batch prompt with full content
        batch_content = self._prepare_tier2_batch(candidates)

        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": f"""You are an expert at identifying and evaluating micro SaaS opportunities.

Analyze these {len(candidates)} threads in detail and select ALL truly promising opportunities. Do not limit yourself - if there are 3 great opportunities, return 3. If there are 15, return 15. Quality matters more than quantity, but don't artificially limit the results.

{batch_content}

For each selected opportunity, provide:
1. **problem_summary**: 2-3 sentence summary of the problem
2. **why_good_opportunity**: Why this is a good business opportunity
3. **key_quotes**: 2-3 direct quotes showing demand
4. **urgency_score**: 1-10 (how urgently do people need this?)
5. **willingness_to_pay_score**: 1-10 (how likely are they to pay?)
6. **market_size_indicator**: "small" | "medium" | "large"
7. **feasibility_score**: 1-10 (how buildable is this?)

Return ONLY a JSON array of ALL promising opportunities:
```json
[
  {{
    "id": "thread_id",
    "problem_summary": "...",
    "why_good_opportunity": "...",
    "key_quotes": ["quote1", "quote2"],
    "urgency_score": 8,
    "willingness_to_pay_score": 7,
    "market_size_indicator": "medium",
    "feasibility_score": 9,
    "opportunity_score": 8.2
  }}
]
```

Be selective about quality, not quantity. Include any opportunity that meets the criteria above."""
                    }
                ]
            )

            # Parse response
            result_text = response.content[0].text.strip()

            # Extract JSON
            if "```json" in result_text:
                start = result_text.find("```json") + 7
                end = result_text.find("```", start)
                result_text = result_text[start:end].strip()

            opportunities = json.loads(result_text)

            # Merge LLM insights back into original candidates
            # No artificial limit - return ALL opportunities Claude selected
            enriched = []
            for opp in opportunities:
                thread_id = opp.get("id")

                # Find original candidate
                for candidate in candidates:
                    if candidate.get("id") == thread_id:
                        # Add LLM insights
                        candidate["llm_analysis"] = {
                            "problem_summary": opp.get("problem_summary"),
                            "why_good_opportunity": opp.get("why_good_opportunity"),
                            "key_quotes": opp.get("key_quotes", []),
                            "urgency_score": opp.get("urgency_score"),
                            "willingness_to_pay_score": opp.get("willingness_to_pay_score"),
                            "market_size_indicator": opp.get("market_size_indicator"),
                            "feasibility_score": opp.get("feasibility_score"),
                            "opportunity_score": opp.get("opportunity_score")
                        }
                        enriched.append(candidate)
                        break

            logger.info(f"Tier 2 selected {len(enriched)} final opportunities")
            return enriched

        except Exception as e:
            logger.error(f"Tier 2 analysis failed: {str(e)}")
            # Fallback: return top N candidates as-is
            return candidates[:limit]

    def _prepare_tier1_batch(self, candidates: List[Dict[str, Any]]) -> str:
        """
        Prepare batch prompt for Tier 1 (GPT-4o-mini)

        Uses title + 500 chars per thread

        Args:
            candidates: List of candidates

        Returns:
            Formatted batch prompt
        """
        threads = []

        for candidate in candidates:
            thread_id = candidate.get("id")
            title = candidate.get("title", "")
            text = candidate.get("text", "")

            # Truncate text to 500 chars
            snippet = f"{title} - {text}"[:500]

            threads.append(f"ID: {thread_id}\n{snippet}\n")

        return "THREADS TO ANALYZE:\n\n" + "\n---\n\n".join(threads)

    def _prepare_tier2_batch(self, candidates: List[Dict[str, Any]]) -> str:
        """
        Prepare batch prompt for Tier 2 (Claude Sonnet)

        Uses full content (up to 2000 chars)

        Args:
            candidates: Top candidates from Tier 1

        Returns:
            Formatted batch prompt
        """
        threads = []

        for candidate in candidates:
            thread_id = candidate.get("id")
            title = candidate.get("title", "")
            text = candidate.get("text", "")
            source = candidate.get("source", "unknown")
            score = candidate.get("score", 0)
            comments = candidate.get("comments", candidate.get("comment_count", 0))

            # Full content up to 2000 chars
            full_content = f"{title} - {text}"[:2000]

            thread_block = f"""
**Thread ID**: {thread_id}
**Source**: {source}
**Engagement**: {score} upvotes, {comments} comments
**Content**: {full_content}
"""
            threads.append(thread_block.strip())

        return "\n\n---\n\n".join(threads)

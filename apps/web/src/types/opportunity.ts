/**
 * TypeScript interfaces for opportunity discovery frontend
 * Based on Multi-Dimensional Opportunity Analysis (6-dimensional scoring)
 */

/**
 * Opportunity list item (lightweight response for browsing)
 * Contains summary data and all 6 dimensional scores
 */
export interface OpportunityListItem {
  /** Unique identifier (UUID) */
  id: string;

  /** Opportunity title (derived from pain point, max 100 chars) */
  title: string;

  /** Brief summary (derived from pain point, max 300 chars) */
  summary: string;

  /** Problem severity score (0-10, higher = more severe pain) */
  problem_severity: number;

  /** Market size indicator */
  market_size: 'niche' | 'mid' | 'large';

  /** Monetization potential score (0-10, higher = better monetization) */
  monetization_potential: number;

  /** Technical complexity score (0-10, higher = more complex to build) */
  technical_complexity: number;

  /** Competition level */
  competition_level: 'low' | 'medium' | 'high' | 'saturated';

  /** Trend direction */
  trend_direction: 'declining' | 'stable' | 'growing' | 'explosive';

  /** LLM confidence level (0-1, higher = more confident analysis) */
  confidence_level: number;

  /** Analysis timestamp (ISO 8601) */
  analyzed_at: string;
}

/**
 * Opportunity detail (full response for detail view)
 * Extends list item with additional metadata
 */
export interface OpportunityDetail extends OpportunityListItem {
  /** Time-series trend data */
  trend_data: {
    timestamps: string[];
    discussion_counts: number[];
    growth_rate: number;
  };

  /** Geographic distribution (e.g., ["US", "UK", "Global"]) */
  geographic_spread: string[];

  /** Affected industries (e.g., ["SaaS", "E-commerce"]) */
  affected_industries: string[];

  /** Source platform where signals originated */
  source_platform: string; // "reddit" | "hackernews"

  /** Number of times this opportunity has been enriched with new signals */
  enrichment_count: number;

  /** Last enrichment timestamp (ISO 8601, null if never enriched) */
  last_enriched_at: string | null;
}

/**
 * Filter state for opportunity queries
 * All fields are optional (omit for no filtering)
 */
export interface OpportunityFilters {
  /** Minimum problem severity (0-10) */
  severity_min?: number;

  /** Maximum problem severity (0-10) */
  severity_max?: number;

  /** Market sizes to include (multi-select) */
  market_size?: ('niche' | 'mid' | 'large')[];

  /** Minimum monetization potential (0-10) */
  monetization_min?: number;

  /** Maximum monetization potential (0-10) */
  monetization_max?: number;

  /** Minimum technical complexity (0-10) */
  complexity_min?: number;

  /** Maximum technical complexity (0-10) */
  complexity_max?: number;

  /** Competition levels to include (multi-select) */
  competition_level?: ('low' | 'medium' | 'high' | 'saturated')[];

  /** Trend directions to include (multi-select) */
  trend_direction?: ('declining' | 'stable' | 'growing' | 'explosive')[];
}

/**
 * Sort field options
 */
export type SortField = 'severity' | 'monetization' | 'analyzed_at' | 'complexity';

/**
 * Sort order options
 */
export type SortOrder = 'asc' | 'desc';

/**
 * API response for opportunities list endpoint
 * Includes pagination metadata
 */
export interface OpportunitiesResponse {
  /** Array of opportunities for current page */
  opportunities: OpportunityListItem[];

  /** Cursor for next page (Base64 encoded, null if no more pages) */
  next_cursor: string | null;

  /** Whether more opportunities exist beyond this page */
  has_more: boolean;
}

/**
 * ScoreBadges Component
 *
 * Displays all 6 dimensional scores as color-coded badges
 * with dark mode support
 */

import type { OpportunityListItem } from '@/types/opportunity';

interface ScoreBadgesProps {
  opportunity: OpportunityListItem;
}

export function ScoreBadges({ opportunity }: ScoreBadgesProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
      {/* Severity Score - Red (high severity bad) */}
      <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-xs font-medium">
        Severity: {opportunity.problem_severity.toFixed(1)}
      </span>

      {/* Market Size - Purple for large, Blue for mid, Yellow for niche */}
      <span
        className={`px-2 py-1 rounded text-xs font-medium ${
          opportunity.market_size === 'large'
            ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
            : opportunity.market_size === 'mid'
            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
            : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
        }`}
      >
        {opportunity.market_size} market
      </span>

      {/* Monetization Potential - Green (high monetization good) */}
      <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-xs font-medium">
        Money: {opportunity.monetization_potential.toFixed(1)}
      </span>

      {/* Technical Complexity - Orange (complexity indicator) */}
      <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded text-xs font-medium">
        Complexity: {opportunity.technical_complexity.toFixed(1)}
      </span>

      {/* Competition Level - Yellow shades */}
      <span
        className={`px-2 py-1 rounded text-xs font-medium ${
          opportunity.competition_level === 'low'
            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
            : opportunity.competition_level === 'saturated'
            ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
            : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
        }`}
      >
        {opportunity.competition_level} comp
      </span>

      {/* Trend Direction - Blue for growing, Green for explosive */}
      <span
        className={`px-2 py-1 rounded text-xs font-medium ${
          opportunity.trend_direction === 'explosive'
            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
            : opportunity.trend_direction === 'growing'
            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
            : opportunity.trend_direction === 'stable'
            ? 'bg-gray-100 dark:bg-gray-800/30 text-gray-700 dark:text-gray-300'
            : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
        }`}
      >
        {opportunity.trend_direction}
      </span>
    </div>
  );
}

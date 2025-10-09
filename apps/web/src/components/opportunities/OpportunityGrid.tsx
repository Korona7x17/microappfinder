/**
 * OpportunityGrid Component
 *
 * Grid container for opportunity cards with:
 * - Responsive layout (1 col mobile, 2 col tablet, 3 col desktop)
 * - Loading state with skeleton loaders
 * - Empty state
 * - "Load More" button for pagination
 * - Dark mode support
 */

import { OpportunityCard } from './OpportunityCard';
import type { OpportunityListItem } from '@/types/opportunity';

interface OpportunityGridProps {
  opportunities: OpportunityListItem[];
  isLoading?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
}

export function OpportunityGrid({
  opportunities,
  isLoading = false,
  hasMore = false,
  onLoadMore,
}: OpportunityGridProps) {
  // Loading state with skeleton loaders (only on initial load)
  if (isLoading && opportunities.length === 0) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 12 }).map((_, i) => (
          <div
            key={i}
            className="h-64 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse"
            aria-label="Loading opportunity"
          />
        ))}
      </div>
    );
  }

  // Empty state
  if (opportunities.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400 text-lg">
          No opportunities match your filters.
        </p>
        <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
          Try adjusting your filter criteria or clear all filters.
        </p>
      </div>
    );
  }

  // Grid with opportunities
  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {opportunities.map((opportunity) => (
          <OpportunityCard key={opportunity.id} opportunity={opportunity} />
        ))}
      </div>

      {/* Load More button */}
      {hasMore && (
        <div className="text-center mt-8">
          <button
            onClick={onLoadMore}
            disabled={isLoading}
            className="px-6 py-3 bg-blue-600 dark:bg-blue-500 text-white rounded-lg text-lg font-medium hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Load more opportunities"
          >
            {isLoading ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}
    </>
  );
}

'use client';

import useSWRInfinite from 'swr/infinite';
import type {
  OpportunityFilters,
  OpportunityListItem,
  OpportunitiesResponse,
  SortField,
  SortOrder,
} from '@/types/opportunity';
import { api } from '@/lib/api';

/**
 * Custom hook for fetching opportunities with filters and cursor-based pagination
 *
 * Uses SWR Infinite for automatic caching, revalidation, and pagination.
 * Supports filtering by all 6 dimensional scores and sorting.
 *
 * @param filters - Optional filter criteria (severity, market size, etc.)
 * @param sortBy - Field to sort by (default: 'analyzed_at')
 * @param sortOrder - Sort order (default: 'desc')
 * @returns Object with opportunities array, loading states, and pagination controls
 *
 * @example
 * ```tsx
 * const { opportunities, isLoading, hasMore, loadMore } = useOpportunities(
 *   { severity_min: 7, market_size: ['large'] },
 *   'monetization',
 *   'desc'
 * );
 * ```
 */
export function useOpportunities(
  filters?: OpportunityFilters,
  sortBy: SortField = 'analyzed_at',
  sortOrder: SortOrder = 'desc'
) {
  /**
   * Generate SWR key for each page
   * Returns null when no more pages (stops fetching)
   */
  const getKey = (
    pageIndex: number,
    previousPageData: OpportunitiesResponse | null
  ) => {
    // Stop if previous page has no more data
    if (previousPageData && !previousPageData.has_more) return null;

    // For first page, no cursor
    if (pageIndex === 0) {
      return ['opportunities', filters, sortBy, sortOrder, undefined];
    }

    // For subsequent pages, use cursor from previous page
    const cursor = previousPageData?.next_cursor;
    return ['opportunities', filters, sortBy, sortOrder, cursor];
  };

  /**
   * Fetcher function for SWR
   * Extracts parameters from the key and calls API
   */
  const fetcher = async (key: any) => {
    const [_keyName, filters, _sortBy, _sortOrder, cursor] = key;
    return api.opportunities.list(filters, cursor, 12);
  };

  // Use SWR Infinite for cursor-based pagination
  const { data, error, size, setSize, isValidating } = useSWRInfinite<OpportunitiesResponse>(
    getKey,
    fetcher,
    {
      revalidateOnFocus: false, // Don't refetch when window regains focus
      revalidateOnReconnect: false, // Don't refetch on network reconnect
      dedupingInterval: 5000, // Dedupe requests within 5 seconds
    }
  );

  /**
   * Flatten paginated data into single array
   * SWR Infinite returns array of pages, we want array of opportunities
   */
  const opportunities: OpportunityListItem[] = data
    ? data.flatMap((page) => page.opportunities)
    : [];

  /**
   * Check if more pages are available
   * Based on last page's has_more flag
   */
  const hasMore = data?.[data.length - 1]?.has_more ?? false;

  /**
   * Loading state: true only on initial load (no data yet)
   * isValidating is true during any fetch (including pagination)
   */
  const isLoading = !data && !error;

  /**
   * Load next page by incrementing size
   * SWR will automatically fetch using the next cursor
   */
  const loadMore = () => {
    setSize(size + 1);
  };

  return {
    opportunities,
    error,
    isLoading,
    isValidating, // True during any fetch (including pagination)
    loadMore,
    hasMore,
  };
}

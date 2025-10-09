/**
 * Opportunities Browse Page
 *
 * Main discovery page with:
 * - FilterPanel (sidebar)
 * - SortControls (header)
 * - OpportunityGrid (main content)
 * - ThemeToggle (top-right corner)
 * - URL-based filter state
 * - Dark mode support
 */

'use client';

// Force dynamic rendering for client-side hooks
export const dynamic = 'force-dynamic';

import { Suspense, useState, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useOpportunities } from '@/hooks/useOpportunities';
import { OpportunityGrid } from '@/components/opportunities/OpportunityGrid';
import { FilterPanel } from '@/components/opportunities/FilterPanel';
import { SortControls } from '@/components/opportunities/SortControls';
import { ThemeToggle } from '@/components/opportunities/ThemeToggle';
import type { OpportunityFilters, SortField, SortOrder } from '@/types/opportunity';

function OpportunitiesContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Parse filters from URL
  const filters: OpportunityFilters = {
    severity_min: searchParams.get('severity_min') ? Number(searchParams.get('severity_min')) : undefined,
    severity_max: searchParams.get('severity_max') ? Number(searchParams.get('severity_max')) : undefined,
    market_size: searchParams.get('market_size')?.split(',') as any,
    monetization_min: searchParams.get('monetization_min') ? Number(searchParams.get('monetization_min')) : undefined,
    monetization_max: searchParams.get('monetization_max') ? Number(searchParams.get('monetization_max')) : undefined,
    complexity_min: searchParams.get('complexity_min') ? Number(searchParams.get('complexity_min')) : undefined,
    complexity_max: searchParams.get('complexity_max') ? Number(searchParams.get('complexity_max')) : undefined,
    competition_level: searchParams.get('competition_level')?.split(',') as any,
    trend_direction: searchParams.get('trend_direction')?.split(',') as any,
  };

  // Parse sort params
  const [sortField, setSortField] = useState<SortField>(
    (searchParams.get('sort') as SortField) || 'analyzed_at'
  );
  const [sortOrder, setSortOrder] = useState<SortOrder>(
    (searchParams.get('order') as SortOrder) || 'desc'
  );

  // Fetch opportunities with current filters
  const { opportunities, isLoading, hasMore, loadMore, isValidating } = useOpportunities(
    filters,
    sortField,
    sortOrder
  );

  // Update URL when filters change
  const handleFilterChange = useCallback((newFilters: OpportunityFilters) => {
    const params = new URLSearchParams();

    // Add all filter params to URL
    if (newFilters.severity_min !== undefined) {
      params.set('severity_min', String(newFilters.severity_min));
    }
    if (newFilters.severity_max !== undefined) {
      params.set('severity_max', String(newFilters.severity_max));
    }
    if (newFilters.market_size && newFilters.market_size.length > 0) {
      params.set('market_size', newFilters.market_size.join(','));
    }
    if (newFilters.monetization_min !== undefined) {
      params.set('monetization_min', String(newFilters.monetization_min));
    }
    if (newFilters.monetization_max !== undefined) {
      params.set('monetization_max', String(newFilters.monetization_max));
    }
    if (newFilters.complexity_min !== undefined) {
      params.set('complexity_min', String(newFilters.complexity_min));
    }
    if (newFilters.complexity_max !== undefined) {
      params.set('complexity_max', String(newFilters.complexity_max));
    }
    if (newFilters.competition_level && newFilters.competition_level.length > 0) {
      params.set('competition_level', newFilters.competition_level.join(','));
    }
    if (newFilters.trend_direction && newFilters.trend_direction.length > 0) {
      params.set('trend_direction', newFilters.trend_direction.join(','));
    }

    // Preserve sort params
    if (sortField !== 'analyzed_at') {
      params.set('sort', sortField);
    }
    if (sortOrder !== 'desc') {
      params.set('order', sortOrder);
    }

    const queryString = params.toString();
    router.push(queryString ? `/opportunities?${queryString}` : '/opportunities');
  }, [router, sortField, sortOrder]);

  // Update URL when sort changes
  const handleSortChange = useCallback((field: SortField, order: SortOrder) => {
    setSortField(field);
    setSortOrder(order);

    const params = new URLSearchParams(searchParams.toString());

    if (field !== 'analyzed_at') {
      params.set('sort', field);
    } else {
      params.delete('sort');
    }

    if (order !== 'desc') {
      params.set('order', order);
    } else {
      params.delete('order');
    }

    const queryString = params.toString();
    router.push(queryString ? `/opportunities?${queryString}` : '/opportunities');
  }, [router, searchParams]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100">
                Discover Opportunities
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {opportunities.length} {opportunities.length === 1 ? 'opportunity' : 'opportunities'} found
              </p>
            </div>
            <div className="flex items-center gap-3 sm:gap-4">
              <SortControls onSortChange={handleSortChange} />
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Filter Panel - Hidden on mobile, shown as sidebar on desktop */}
          <aside className="hidden lg:block lg:w-64 flex-shrink-0">
            <div className="sticky top-24">
              <FilterPanel onFilterChange={handleFilterChange} />
            </div>
          </aside>

          {/* Mobile Filter Panel - Could be implemented as a Sheet/Modal */}
          <div className="lg:hidden">
            <details className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-4">
              <summary className="font-semibold text-gray-900 dark:text-gray-100 cursor-pointer">
                Filters & Sort
              </summary>
              <div className="mt-4">
                <FilterPanel onFilterChange={handleFilterChange} />
              </div>
            </details>
          </div>

          {/* Opportunity Grid */}
          <div className="flex-1 min-w-0">
            <OpportunityGrid
              opportunities={opportunities}
              isLoading={isLoading || isValidating}
              hasMore={hasMore}
              onLoadMore={loadMore}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default function OpportunitiesPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading opportunities...</p>
        </div>
      </div>
    }>
      <OpportunitiesContent />
    </Suspense>
  );
}

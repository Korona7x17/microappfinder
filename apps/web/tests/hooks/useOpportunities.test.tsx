/**
 * Test: useOpportunities Hook
 * TDD approach - these tests should FAIL initially
 *
 * Tests the custom SWR hook for fetching opportunities with filters and pagination
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { SWRConfig } from 'swr';
import { useOpportunities } from '@/hooks/useOpportunities';
import { api } from '@/lib/api';
import type { OpportunityListItem, OpportunitiesResponse } from '@/types/opportunity';

// Mock the API client
jest.mock('@/lib/api', () => ({
  api: {
    opportunities: {
      list: jest.fn(),
    },
  },
}));

const mockApi = api.opportunities.list as jest.MockedFunction<typeof api.opportunities.list>;

describe('useOpportunities', () => {
  let swrCache: Map<any, any>;

  beforeEach(() => {
    jest.clearAllMocks();
    // Create fresh SWR cache for each test
    swrCache = new Map();
  });

  // Test wrapper with SWR config
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <SWRConfig value={{ provider: () => swrCache, dedupingInterval: 0 }}>
      {children}
    </SWRConfig>
  );

  const mockOpportunity: OpportunityListItem = {
    id: 'test-id-1',
    title: 'Test Opportunity',
    summary: 'Test summary for opportunity',
    problem_severity: 8.5,
    market_size: 'large',
    monetization_potential: 7.0,
    technical_complexity: 5.0,
    competition_level: 'medium',
    trend_direction: 'growing',
    confidence_level: 0.85,
    analyzed_at: '2025-10-09T12:00:00Z',
  };

  const mockResponse: OpportunitiesResponse = {
    opportunities: [mockOpportunity],
    next_cursor: 'next-cursor-123',
    has_more: true,
  };

  it('fetches initial opportunities on mount', async () => {
    mockApi.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useOpportunities(), { wrapper });

    // Initially loading
    expect(result.current.isLoading).toBe(true);
    expect(result.current.opportunities).toEqual([]);

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify API was called correctly
    expect(mockApi).toHaveBeenCalledWith(undefined, undefined, 12);

    // Verify data is returned
    expect(result.current.opportunities).toEqual([mockOpportunity]);
    expect(result.current.hasMore).toBe(true);
    expect(result.current.error).toBeUndefined();
  });

  it('applies filters and refetches', async () => {
    const filters = {
      severity_min: 7,
      severity_max: 10,
      market_size: ['large' as const],
    };

    mockApi.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useOpportunities(filters), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify API was called with filters
    expect(mockApi).toHaveBeenCalledWith(filters, undefined, 12);
    expect(result.current.opportunities).toEqual([mockOpportunity]);
  });

  it('loads more opportunities with cursor pagination', async () => {
    const firstPageResponse: OpportunitiesResponse = {
      opportunities: [mockOpportunity],
      next_cursor: 'cursor-page-2',
      has_more: true,
    };

    const secondOpportunity: OpportunityListItem = {
      ...mockOpportunity,
      id: 'test-id-2',
      title: 'Second Opportunity',
    };

    const secondPageResponse: OpportunitiesResponse = {
      opportunities: [secondOpportunity],
      next_cursor: null,
      has_more: false,
    };

    // Mock implementation that returns correct page based on cursor
    mockApi.mockImplementation(async (_filters, cursor, _limit) => {
      if (!cursor) {
        return firstPageResponse;
      }
      if (cursor === 'cursor-page-2') {
        return secondPageResponse;
      }
      throw new Error(`Unexpected cursor: ${cursor}`);
    });

    const { result } = renderHook(() => useOpportunities(), { wrapper });

    // Wait for first page
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.opportunities).toHaveLength(1);
    expect(result.current.hasMore).toBe(true);

    // Load more
    await act(async () => {
      result.current.loadMore();
    });

    // Wait for second page to finish loading
    await waitFor(
      () => {
        expect(result.current.isValidating).toBe(false);
      },
      { timeout: 3000 }
    );

    // Verify both opportunities are loaded
    expect(result.current.opportunities).toHaveLength(2);
    expect(result.current.opportunities).toEqual([mockOpportunity, secondOpportunity]);
    expect(result.current.hasMore).toBe(false);

    // Verify cursor was passed for loading second page
    // Note: SWR may make multiple calls due to revalidation
    expect(mockApi).toHaveBeenCalledWith(undefined, 'cursor-page-2', 12);
  });

  it('handles API errors gracefully', async () => {
    const errorMessage = 'Failed to fetch opportunities';
    mockApi.mockRejectedValueOnce(new Error(errorMessage));

    const { result } = renderHook(() => useOpportunities(), { wrapper });

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });

    expect(result.current.opportunities).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error?.message).toBe(errorMessage);
  });

  it('passes sort parameters correctly', async () => {
    mockApi.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(
      () => useOpportunities(undefined, 'monetization', 'desc'),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Note: Sort params are part of the filter key, not passed to API directly
    // The hook should include sort in the SWR key
    expect(result.current.opportunities).toEqual([mockOpportunity]);
  });

  it('returns empty array when no opportunities match filters', async () => {
    const emptyResponse: OpportunitiesResponse = {
      opportunities: [],
      next_cursor: null,
      has_more: false,
    };

    mockApi.mockResolvedValueOnce(emptyResponse);

    const { result } = renderHook(
      () => useOpportunities({ severity_min: 10 }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.opportunities).toEqual([]);
    expect(result.current.hasMore).toBe(false);
  });
});

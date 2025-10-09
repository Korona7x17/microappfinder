/**
 * T042: API client
 * Fetch wrapper with cookie credentials and TypeScript types
 */

import type {
  OpportunityListItem,
  OpportunityDetail,
  OpportunityFilters,
  OpportunitiesResponse,
} from '@/types/opportunity';

// API Base URL from environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Debug logging
if (typeof window !== 'undefined') {
  console.log('🔍 API_BASE_URL:', API_BASE_URL);
  console.log('🔍 NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
}

// API Error class
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public response?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Request options interface
interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
}

/**
 * Core fetch wrapper with error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { params, ...fetchOptions } = options;

  // Build URL with query parameters
  let url = `${API_BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      searchParams.append(key, String(value));
    });
    url += `?${searchParams.toString()}`;
  }

  // Default options
  const defaultOptions: RequestInit = {
    credentials: 'include', // Include cookies for auth
    headers: {
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    },
  };

  console.log('🌐 Fetching:', url);
  const response = await fetch(url, { ...defaultOptions, ...fetchOptions });

  // Handle non-OK responses
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    let errorData;

    try {
      errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // Response not JSON, use default message
    }

    throw new APIError(errorMessage, response.status, errorData);
  }

  // Parse JSON response
  try {
    return await response.json();
  } catch {
    // No JSON body (e.g., 204 No Content)
    return {} as T;
  }
}

// TypeScript interfaces for API responses

export interface AuthResponse {
  user_id: string;
  message: string;
}

export interface UserProfile {
  user_id: string;
  email: string;
  created_at: string;
  total_searches: number;
}

export interface SearchRunCreated {
  search_run_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  message: string;
}

export interface SearchRunStatus {
  search_run_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  topics: string[];
  time_range: '24h' | '7days' | '30days' | '90days' | '1year' | 'all';
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  pain_points_count: number;
  error_message: string | null;
}

export interface PainPoint {
  id: string;
  extracted_text: string;
  relevance_score: number;
  sentiment_score: number;
  llm_insights?: {
    problem_summary: string;
    why_good_opportunity: string;
    key_quotes: string[];
    urgency_score: number;
    willingness_to_pay_score: number;
    market_size_indicator: 'small' | 'medium' | 'large';
    feasibility_score: number;
    opportunity_score: number;
  };
  source_platform: string;
  source_post_ids: string[];
  source_deleted: boolean;
  created_at: string;
  topics: string[];
}

export interface PaginatedPainPoints {
  search_run_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  pain_points: PainPoint[];
  total: number;
  page: number;
  limit: number;
  message?: string;
}

export interface RecentSearchRun {
  search_run_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  topics: string[];
  created_at: string;
  pain_points_count: number;
}

export interface UserDashboard {
  recent_runs: RecentSearchRun[];
  total_searches: number;
  recent_pain_points: PainPoint[];
}

// API Client
export const api = {
  // Authentication
  auth: {
    register: (email: string, password: string) =>
      fetchAPI<AuthResponse>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),

    login: (email: string, password: string) =>
      fetchAPI<AuthResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),

    logout: () =>
      fetchAPI<{ message: string }>('/api/auth/logout', {
        method: 'POST',
      }),

    refresh: () =>
      fetchAPI<{ message: string }>('/api/auth/refresh', {
        method: 'POST',
      }),

    getMe: () => fetchAPI<UserProfile>('/api/auth/me'),
  },

  // Reddit Search
  reddit: {
    createSearch: (topics: string[], timeRange: string) =>
      fetchAPI<SearchRunCreated>('/api/reddit/search', {
        method: 'POST',
        body: JSON.stringify({ topics, time_range: timeRange }),
      }),

    getSearchStatus: (searchRunId: string) =>
      fetchAPI<SearchRunStatus>(`/api/reddit/search/${searchRunId}`),

    getSearchResults: (searchRunId: string, page = 1, limit = 50) =>
      fetchAPI<PaginatedPainPoints>(
        `/api/reddit/search/${searchRunId}/results`,
        {
          params: { page, limit },
        }
      ),

    deleteSearch: (searchRunId: string) =>
      fetchAPI<{ message: string; search_run_id: string }>(
        `/api/reddit/search/${searchRunId}`,
        {
          method: 'DELETE',
        }
      ),

    retrySearch: (searchRunId: string) =>
      fetchAPI<SearchRunCreated>(
        `/api/reddit/search/${searchRunId}/retry`,
        {
          method: 'POST',
        }
      ),

    getRecent: (limit = 20) =>
      fetchAPI<PaginatedPainPoints>('/api/reddit/recent', {
        params: { limit },
      }),

    getDashboard: () => fetchAPI<UserDashboard>('/api/reddit/dashboard'),
  },

  // Opportunities
  opportunities: {
    /**
     * List opportunities with optional filters and pagination
     * @param filters - Optional filter criteria for opportunities
     * @param cursor - Base64 encoded cursor for pagination
     * @param limit - Number of results per page (default: 12, max: 50)
     * @returns Paginated opportunities response
     */
    list: async (
      filters?: OpportunityFilters,
      cursor?: string,
      limit: number = 12
    ): Promise<OpportunitiesResponse> => {
      const params = new URLSearchParams();

      // Add filter parameters
      if (filters) {
        if (filters.severity_min !== undefined) {
          params.set('severity_min', String(filters.severity_min));
        }
        if (filters.severity_max !== undefined) {
          params.set('severity_max', String(filters.severity_max));
        }
        if (filters.market_size && filters.market_size.length > 0) {
          params.set('market_size', filters.market_size.join(','));
        }
        if (filters.monetization_min !== undefined) {
          params.set('monetization_min', String(filters.monetization_min));
        }
        if (filters.monetization_max !== undefined) {
          params.set('monetization_max', String(filters.monetization_max));
        }
        if (filters.complexity_min !== undefined) {
          params.set('complexity_min', String(filters.complexity_min));
        }
        if (filters.complexity_max !== undefined) {
          params.set('complexity_max', String(filters.complexity_max));
        }
        if (filters.competition_level && filters.competition_level.length > 0) {
          params.set('competition_level', filters.competition_level.join(','));
        }
        if (filters.trend_direction && filters.trend_direction.length > 0) {
          params.set('trend_direction', filters.trend_direction.join(','));
        }
      }

      // Add pagination parameters
      if (cursor) {
        params.set('cursor', cursor);
      }
      params.set('limit', String(limit));

      const queryString = params.toString();
      const url = `/api/opportunities${queryString ? `?${queryString}` : ''}`;

      return fetchAPI<OpportunitiesResponse>(url);
    },

    /**
     * Get a single opportunity by ID
     * @param id - Opportunity UUID
     * @returns Full opportunity details
     * @throws APIError with status 404 if opportunity not found
     */
    getById: (id: string): Promise<OpportunityDetail> => {
      return fetchAPI<OpportunityDetail>(`/api/opportunities/${id}`);
    },
  },
};

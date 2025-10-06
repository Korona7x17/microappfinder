/**
 * T042: API client
 * Fetch wrapper with cookie credentials and TypeScript types
 */

// API Base URL from environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
};

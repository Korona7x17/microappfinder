/**
 * Search Results Page
 * Displays pain points from a completed search run
 */
'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ProtectedRoute } from '@/lib/auth';
import { api, PaginatedPainPoints, SearchRunStatus } from '@/lib/api';

export default function SearchResultsPage() {
  return (
    <ProtectedRoute>
      <SearchResultsContent />
    </ProtectedRoute>
  );
}

function SearchResultsContent() {
  const router = useRouter();
  const params = useParams();
  const searchRunId = params.id as string;

  const [status, setStatus] = useState<SearchRunStatus | null>(null);
  const [results, setResults] = useState<PaginatedPainPoints | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const loadSearchStatus = async () => {
    try {
      const data = await api.reddit.getSearchStatus(searchRunId);
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load search status');
    }
  };

  const loadResults = async (page = 1) => {
    try {
      setLoading(true);
      const data = await api.reddit.getSearchResults(searchRunId, page, 50);
      setResults(data);
      setCurrentPage(page);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSearchStatus();
    loadResults();
  }, [searchRunId]);

  if (loading && !results) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="space-y-4">
              <div className="h-32 bg-gray-200 rounded"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </button>

          {status && (
            <>
              <div className="flex items-center gap-4 mb-4">
                <h1 className="text-3xl font-bold text-gray-900">Search Results</h1>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    status.status === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : status.status === 'failed'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}
                >
                  {status.status}
                </span>

                {status.status === 'failed' && (
                  <button
                    onClick={async () => {
                      try {
                        await api.reddit.retrySearch(searchRunId);
                        // Reload status and results
                        await loadSearchStatus();
                        setResults(null); // Clear old results
                      } catch (err) {
                        setError(err instanceof Error ? err.message : 'Failed to retry search');
                      }
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Retry Search
                  </button>
                )}
              </div>

              <div className="flex flex-wrap gap-2 mb-2">
                {status.topics.map((topic, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                  >
                    {topic}
                  </span>
                ))}
              </div>

              <p className="text-gray-600">
                {status.status === 'completed' && results && (
                  <>Found {results.total} pain points • {new Date(status.created_at).toLocaleString()}</>
                )}
                {status.status === 'in_progress' && 'Search in progress...'}
                {status.status === 'pending' && 'Search pending...'}
                {status.status === 'failed' && `Search failed: ${status.error_message}`}
              </p>
            </>
          )}
        </div>

        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Results */}
        {results && results.pain_points && results.pain_points.length > 0 ? (
          <>
            <div className="space-y-4 mb-8">
              {results.pain_points.map((painPoint) => (
                <div
                  key={painPoint.id}
                  className="bg-white shadow rounded-lg p-6 border-l-4 border-blue-500"
                >
                  <p className="text-gray-900 mb-4 text-lg">{painPoint.extracted_text}</p>

                  <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">Relevance:</span>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                        {(painPoint.relevance_score * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="font-medium">Sentiment:</span>
                      <span
                        className={`px-2 py-1 rounded ${
                          painPoint.sentiment_score < -0.3
                            ? 'bg-red-100 text-red-800'
                            : painPoint.sentiment_score > 0.3
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {painPoint.sentiment_score.toFixed(2)}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="font-medium">Source:</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        painPoint.source_platform === 'hackernews'
                          ? 'bg-orange-100 text-orange-800'
                          : 'bg-purple-100 text-purple-800'
                      }`}>
                        {painPoint.source_platform === 'hackernews' ? 'HackerNews' : 'Reddit'}
                      </span>
                      <span className="text-gray-500 text-xs">
                        ({painPoint.source_post_ids?.length || 0} posts)
                      </span>
                    </div>
                  </div>

                  {painPoint.topics && painPoint.topics.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {painPoint.topics.map((topic, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Pagination */}
            {results.total > 50 && (
              <div className="flex justify-center items-center gap-4">
                <button
                  onClick={() => loadResults(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Previous
                </button>

                <span className="text-gray-600">
                  Page {currentPage} of {Math.ceil(results.total / 50)}
                </span>

                <button
                  onClick={() => loadResults(currentPage + 1)}
                  disabled={currentPage >= Math.ceil(results.total / 50)}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="bg-white shadow rounded-lg p-12 text-center">
            <p className="text-gray-500 text-lg">
              {status?.status === 'completed'
                ? 'No pain points found for this search.'
                : status?.status === 'in_progress'
                ? 'Search is still processing. Please check back soon.'
                : status?.status === 'pending'
                ? 'Search is queued and will start shortly.'
                : 'Unable to load results.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

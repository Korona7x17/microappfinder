/**
 * T041: Dashboard page
 * User dashboard with recent searches and pain points
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/lib/auth';
import { api, UserDashboard } from '@/lib/api';
import SearchForm from '@/components/search/SearchForm';
import RunStatus from '@/components/search/RunStatus';

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}

function DashboardContent() {
  const router = useRouter();
  const [dashboard, setDashboard] = useState<UserDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeSearchId, setActiveSearchId] = useState<string | null>(null);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await api.reddit.getDashboard();
      setDashboard(data);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const handleSearchCreated = (searchRunId: string) => {
    setActiveSearchId(searchRunId);
    loadDashboard(); // Refresh dashboard
  };

  const handleSearchCompleted = () => {
    loadDashboard(); // Refresh dashboard when search completes
  };

  const handleDeleteSearch = async (searchRunId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent navigation

    if (!confirm('Delete this search? This cannot be undone.')) {
      return;
    }

    try {
      await api.reddit.deleteSearch(searchRunId);
      if (activeSearchId === searchRunId) {
        setActiveSearchId(null);
      }
      loadDashboard(); // Refresh dashboard
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete search');
    }
  };

  if (loading && !dashboard) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="h-96 bg-gray-200 rounded"></div>
              <div className="h-96 bg-gray-200 rounded lg:col-span-2"></div>
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
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          {dashboard && (
            <p className="text-gray-600 mt-2">
              Total searches: <span className="font-semibold">{dashboard.total_searches}</span>
            </p>
          )}
        </div>

        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Search Form */}
          <div className="lg:col-span-1">
            <SearchForm onSearchCreated={handleSearchCreated} />
          </div>

          {/* Right Column: Recent Activity */}
          <div className="lg:col-span-2 space-y-6">
            {/* Active Search Status */}
            {activeSearchId && (
              <RunStatus
                searchRunId={activeSearchId}
                onCompleted={handleSearchCompleted}
              />
            )}

            {/* Recent Searches */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">Recent Searches</h2>

              {!dashboard || dashboard.recent_runs.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No searches yet. Start your first search!
                </p>
              ) : (
                <div className="space-y-3">
                  {dashboard.recent_runs.map((run) => (
                    <div
                      key={run.search_run_id}
                      className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 cursor-pointer"
                      onClick={() => router.push(`/search/${run.search_run_id}`)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex flex-wrap gap-2 mb-2">
                            {run.topics.map((topic, i) => (
                              <span
                                key={i}
                                className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm"
                              >
                                {topic}
                              </span>
                            ))}
                          </div>
                          <p className="text-xs text-gray-500">
                            {new Date(run.created_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="ml-4 flex items-center gap-2">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-medium ${
                              run.status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : run.status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}
                          >
                            {run.status === 'completed'
                              ? `${run.pain_points_count} found`
                              : run.status}
                          </span>
                          <button
                            onClick={(e) => handleDeleteSearch(run.search_run_id, e)}
                            className="text-gray-400 hover:text-red-600 transition-colors"
                            title="Delete search"
                          >
                            <svg
                              className="w-5 h-5"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Pain Points Preview */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">Recent Pain Points</h2>

              {!dashboard || dashboard.recent_pain_points.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No recent pain points. Complete a search to see results!
                </p>
              ) : (
                <div className="space-y-4">
                  {dashboard.recent_pain_points.slice(0, 10).map((painPoint) => (
                    <div key={painPoint.id} className="border-l-4 border-blue-500 pl-4">
                      <p className="text-sm text-gray-900 mb-2">
                        {painPoint.extracted_text}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>
                          Relevance: {(painPoint.relevance_score * 100).toFixed(1)}%
                        </span>
                        <span>
                          Sentiment: {painPoint.sentiment_score.toFixed(2)}
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {painPoint.topics.slice(0, 2).map((topic, i) => (
                            <span
                              key={i}
                              className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded"
                            >
                              {topic}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

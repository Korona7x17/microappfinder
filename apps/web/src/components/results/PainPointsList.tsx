/**
 * T040: Pain points list
 * Paginated table of pain points with relevance scores
 */

'use client';

import { useState, useEffect } from 'react';
import { api, PainPoint, PaginatedPainPoints } from '@/lib/api';

interface PainPointsListProps {
  searchRunId: string;
}

export default function PainPointsList({ searchRunId }: PainPointsListProps) {
  const [data, setData] = useState<PaginatedPainPoints | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const limit = 50;

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        const results = await api.reddit.getSearchResults(searchRunId, page, limit);
        setData(results);
        setError('');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch results');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [searchRunId, page]);

  if (loading && !data) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Handle non-completed searches
  if (data.status !== 'completed') {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-8">
          <p className="text-gray-600">
            {data.message || 'Search is still processing...'}
          </p>
        </div>
      </div>
    );
  }

  // No results
  if (data.pain_points.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-8">
          <p className="text-gray-600 text-lg">No pain points found for this search.</p>
          <p className="text-gray-500 text-sm mt-2">
            Try different topics or a wider time range.
          </p>
        </div>
      </div>
    );
  }

  const totalPages = Math.ceil(data.total / limit);

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold">
          Pain Points ({data.total} found)
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Pain Point
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                Relevance
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                Sentiment
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                Sources
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.pain_points.map((painPoint) => (
              <tr key={painPoint.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <p className="text-sm text-gray-900">{painPoint.extracted_text}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {painPoint.topics.map((topic, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center">
                    <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${painPoint.relevance_score * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      {(painPoint.relevance_score * 100).toFixed(1)}%
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      painPoint.sentiment_score < -0.3
                        ? 'bg-red-100 text-red-800'
                        : painPoint.sentiment_score > 0.3
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {painPoint.sentiment_score > 0 ? '+' : ''}
                    {painPoint.sentiment_score.toFixed(2)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-col space-y-1">
                    {painPoint.source_reddit_post_ids.slice(0, 2).map((postId, i) => (
                      <a
                        key={i}
                        href={`https://reddit.com/${postId}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        Reddit
                      </a>
                    ))}
                    {painPoint.source_reddit_post_ids.length > 2 && (
                      <span className="text-xs text-gray-500">
                        +{painPoint.source_reddit_post_ids.length - 2} more
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Page {page} of {totalPages}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

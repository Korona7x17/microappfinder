/**
 * T039: Run status component
 * Poll and display search run status with progress indicator
 */

'use client';

import { useState, useEffect } from 'react';
import { api, SearchRunStatus } from '@/lib/api';

interface RunStatusProps {
  searchRunId: string;
  onCompleted?: () => void;
}

const STATUS_COLORS = {
  pending: 'bg-yellow-100 text-yellow-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const STATUS_LABELS = {
  pending: 'Pending',
  in_progress: 'Processing',
  completed: 'Completed',
  failed: 'Failed',
};

export default function RunStatus({ searchRunId, onCompleted }: RunStatusProps) {
  const [status, setStatus] = useState<SearchRunStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const fetchStatus = async () => {
      try {
        const data = await api.reddit.getSearchStatus(searchRunId);
        setStatus(data);
        setError('');

        // Stop polling if completed or failed
        if (data.status === 'completed' || data.status === 'failed') {
          if (intervalId) {
            clearInterval(intervalId);
          }

          if (data.status === 'completed' && onCompleted) {
            onCompleted();
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchStatus();

    // Poll every 2 seconds
    intervalId = setInterval(fetchStatus, 2000);

    // Cleanup
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [searchRunId, onCompleted]);

  if (loading && !status) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
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

  if (!status) {
    return null;
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Search Status</h3>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            STATUS_COLORS[status.status]
          }`}
        >
          {STATUS_LABELS[status.status]}
        </span>
      </div>

      <div className="space-y-3">
        <div>
          <p className="text-sm text-gray-600">Topics:</p>
          <div className="flex flex-wrap gap-2 mt-1">
            {status.topics.map((topic, i) => (
              <span
                key={i}
                className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm"
              >
                {topic}
              </span>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm text-gray-600">Time Range:</p>
          <p className="text-sm font-medium">{status.time_range}</p>
        </div>

        {status.status === 'completed' && (
          <div>
            <p className="text-sm text-gray-600">Pain Points Found:</p>
            <p className="text-2xl font-bold text-blue-600">
              {status.pain_points_count}
            </p>
          </div>
        )}

        {status.status === 'failed' && status.error_message && (
          <div className="rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{status.error_message}</p>
          </div>
        )}

        {(status.status === 'pending' || status.status === 'in_progress') && (
          <div className="pt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse w-2/3"></div>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {status.status === 'pending'
                ? 'Waiting to start...'
                : 'Searching and extracting pain points...'}
            </p>
          </div>
        )}

        <div className="text-xs text-gray-500 pt-2 border-t">
          <p>Created: {new Date(status.created_at).toLocaleString()}</p>
          {status.completed_at && (
            <p>Completed: {new Date(status.completed_at).toLocaleString()}</p>
          )}
        </div>
      </div>
    </div>
  );
}

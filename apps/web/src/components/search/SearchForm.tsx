/**
 * T038: Search form component
 * Form for creating Reddit pain point discovery searches
 */

'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

interface SearchFormProps {
  onSearchCreated?: (searchRunId: string) => void;
}

const TIME_RANGES = [
  { value: '24h', label: 'Last 24 hours' },
  { value: '7days', label: 'Last 7 days' },
  { value: '30days', label: 'Last 30 days' },
  { value: '90days', label: 'Last 90 days' },
  { value: '1year', label: 'Last year' },
  { value: 'all', label: 'All time' },
];

export default function SearchForm({ onSearchCreated }: SearchFormProps) {
  const [topics, setTopics] = useState('');
  const [timeRange, setTimeRange] = useState('7days');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Parse topics (one per line)
      const topicList = topics
        .split('\n')
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      // Validate topics
      if (topicList.length === 0) {
        setError('Please enter at least one topic');
        return;
      }

      if (topicList.length > 5) {
        setError('Maximum 5 topics allowed');
        return;
      }

      // Validate topic length
      for (const topic of topicList) {
        if (topic.length < 2 || topic.length > 100) {
          setError(`Topic "${topic}" must be 2-100 characters`);
          return;
        }

        // Validate alphanumeric + spaces only
        if (!/^[a-zA-Z0-9\s]+$/.test(topic)) {
          setError(`Topic "${topic}" can only contain letters, numbers, and spaces`);
          return;
        }
      }

      // Create search
      const result = await api.reddit.createSearch(topicList, timeRange);

      // Clear form
      setTopics('');
      setTimeRange('7days');

      // Notify parent
      if (onSearchCreated) {
        onSearchCreated(result.search_run_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create search');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Start a New Search</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div>
          <label
            htmlFor="topics"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Topics (1-5, one per line)
          </label>
          <textarea
            id="topics"
            rows={5}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="productivity tools&#10;time management&#10;project tracking"
            value={topics}
            onChange={(e) => setTopics(e.target.value)}
            required
          />
          <p className="mt-1 text-sm text-gray-500">
            Enter 1-5 search topics. Each topic must be 2-100 characters (letters, numbers, and spaces only).
          </p>
        </div>

        <div>
          <label
            htmlFor="timeRange"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Time Range
          </label>
          <select
            id="timeRange"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            {TIME_RANGES.map((range) => (
              <option key={range.value} value={range.value}>
                {range.label}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Starting search...' : 'Start Search'}
        </button>
      </form>
    </div>
  );
}

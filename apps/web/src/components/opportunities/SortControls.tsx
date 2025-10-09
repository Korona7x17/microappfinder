/**
 * SortControls Component
 *
 * Dropdown for sorting opportunities by any dimensional score
 * with order toggle (ASC/DESC) and dark mode support
 */

'use client';

import { useState } from 'react';
import type { SortField, SortOrder } from '@/types/opportunity';

interface SortControlsProps {
  onSortChange: (field: SortField, order: SortOrder) => void;
}

export function SortControls({ onSortChange }: SortControlsProps) {
  const [sortField, setSortField] = useState<SortField>('analyzed_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const handleFieldChange = (field: SortField) => {
    setSortField(field);
    onSortChange(field, sortOrder);
  };

  const toggleOrder = () => {
    const newOrder: SortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    setSortOrder(newOrder);
    onSortChange(sortField, newOrder);
  };

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="sort-select" className="text-sm font-medium text-gray-700 dark:text-gray-300 sr-only">
        Sort by
      </label>
      <select
        id="sort-select"
        value={sortField}
        onChange={(e) => handleFieldChange(e.target.value as SortField)}
        className="px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-colors"
        aria-label="Sort field"
      >
        <option value="analyzed_at">Latest</option>
        <option value="severity">Severity</option>
        <option value="monetization">Monetization</option>
        <option value="complexity">Complexity</option>
      </select>

      <button
        onClick={toggleOrder}
        className="px-3 py-2 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors text-sm font-medium"
        aria-label={`Sort order: ${sortOrder === 'asc' ? 'Ascending' : 'Descending'}`}
        title={sortOrder === 'asc' ? 'Ascending order' : 'Descending order'}
      >
        {sortOrder === 'asc' ? '↑' : '↓'}
      </button>
    </div>
  );
}

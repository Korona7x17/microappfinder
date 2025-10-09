/**
 * FilterPanel Component
 *
 * Side panel with 6 dimensional filters:
 * - 3 range inputs: Severity, Monetization, Complexity
 * - 3 multi-selects: Market Size, Competition Level, Trend Direction
 * - Debounced updates (300ms)
 * - Clear Filters button
 * - Dark mode support
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import type { OpportunityFilters } from '@/types/opportunity';

interface FilterPanelProps {
  onFilterChange: (filters: OpportunityFilters) => void;
}

export function FilterPanel({ onFilterChange }: FilterPanelProps) {
  const [filters, setFilters] = useState<OpportunityFilters>({});
  const debouncedFilters = useDebounce(filters, 300);
  const isInitialMount = useRef(true);

  // Call onFilterChange when debounced filters change (skip initial mount)
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    onFilterChange(debouncedFilters);
  }, [debouncedFilters, onFilterChange]);

  const updateSeverity = (field: 'severity_min' | 'severity_max', value: string) => {
    const numValue = value === '' ? undefined : Number(value);
    setFilters((prev) => ({ ...prev, [field]: numValue }));
  };

  const updateMonetization = (field: 'monetization_min' | 'monetization_max', value: string) => {
    const numValue = value === '' ? undefined : Number(value);
    setFilters((prev) => ({ ...prev, [field]: numValue }));
  };

  const updateComplexity = (field: 'complexity_min' | 'complexity_max', value: string) => {
    const numValue = value === '' ? undefined : Number(value);
    setFilters((prev) => ({ ...prev, [field]: numValue }));
  };

  const toggleMarketSize = (size: 'niche' | 'mid' | 'large') => {
    setFilters((prev) => {
      const current = prev.market_size || [];
      const newMarketSize = current.includes(size)
        ? current.filter((s) => s !== size)
        : [...current, size];
      return {
        ...prev,
        market_size: newMarketSize.length > 0 ? newMarketSize : undefined,
      };
    });
  };

  const toggleCompetition = (level: 'low' | 'medium' | 'high' | 'saturated') => {
    setFilters((prev) => {
      const current = prev.competition_level || [];
      const newCompetition = current.includes(level)
        ? current.filter((l) => l !== level)
        : [...current, level];
      return {
        ...prev,
        competition_level: newCompetition.length > 0 ? newCompetition : undefined,
      };
    });
  };

  const toggleTrend = (direction: 'declining' | 'stable' | 'growing' | 'explosive') => {
    setFilters((prev) => {
      const current = prev.trend_direction || [];
      const newTrend = current.includes(direction)
        ? current.filter((d) => d !== direction)
        : [...current, direction];
      return {
        ...prev,
        trend_direction: newTrend.length > 0 ? newTrend : undefined,
      };
    });
  };

  const clearFilters = () => {
    setFilters({});
  };

  return (
    <aside className="w-64 bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-6">
      <h2 className="text-xl font-bold mb-6 text-gray-900 dark:text-gray-100">Filters</h2>

      {/* Severity Range */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-3 text-gray-700 dark:text-gray-300">
          Problem Severity
        </label>
        <div className="space-y-2">
          <div>
            <label htmlFor="severity-min" className="text-xs text-gray-600 dark:text-gray-400">
              Min (0-10)
            </label>
            <input
              id="severity-min"
              type="number"
              min="0"
              max="10"
              step="0.1"
              value={filters.severity_min ?? ''}
              onChange={(e) => updateSeverity('severity_min', e.target.value)}
              className="w-full px-2 py-1 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
              aria-label="Severity min"
            />
          </div>
          <div>
            <label htmlFor="severity-max" className="text-xs text-gray-600 dark:text-gray-400">
              Max (0-10)
            </label>
            <input
              id="severity-max"
              type="number"
              min="0"
              max="10"
              step="0.1"
              value={filters.severity_max ?? ''}
              onChange={(e) => updateSeverity('severity_max', e.target.value)}
              className="w-full px-2 py-1 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
              aria-label="Severity max"
            />
          </div>
        </div>
      </div>

      {/* Market Size Multi-Select */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
          Market Size
        </label>
        <div className="space-y-2">
          {(['niche', 'mid', 'large'] as const).map((size) => (
            <label key={size} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.market_size?.includes(size) || false}
                onChange={() => toggleMarketSize(size)}
                className="mr-2"
                aria-label={size}
              />
              <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">{size}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Monetization Range */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-3 text-gray-700 dark:text-gray-300">
          Monetization Potential
        </label>
        <div className="space-y-2">
          <div>
            <label htmlFor="monetization-min" className="text-xs text-gray-600 dark:text-gray-400">
              Min (0-10)
            </label>
            <input
              id="monetization-min"
              type="number"
              min="0"
              max="10"
              step="0.1"
              value={filters.monetization_min ?? ''}
              onChange={(e) => updateMonetization('monetization_min', e.target.value)}
              className="w-full px-2 py-1 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Complexity Range */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-3 text-gray-700 dark:text-gray-300">
          Technical Complexity
        </label>
        <div className="space-y-2">
          <div>
            <label htmlFor="complexity-max" className="text-xs text-gray-600 dark:text-gray-400">
              Max (0-10)
            </label>
            <input
              id="complexity-max"
              type="number"
              min="0"
              max="10"
              step="0.1"
              value={filters.complexity_max ?? ''}
              onChange={(e) => updateComplexity('complexity_max', e.target.value)}
              className="w-full px-2 py-1 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Competition Level Multi-Select */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
          Competition Level
        </label>
        <div className="space-y-2">
          {(['low', 'medium', 'high', 'saturated'] as const).map((level) => (
            <label key={level} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.competition_level?.includes(level) || false}
                onChange={() => toggleCompetition(level)}
                className="mr-2"
                aria-label={level}
              />
              <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">{level}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Trend Direction Multi-Select */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
          Trend Direction
        </label>
        <div className="space-y-2">
          {(['declining', 'stable', 'growing', 'explosive'] as const).map((trend) => (
            <label key={trend} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.trend_direction?.includes(trend) || false}
                onChange={() => toggleTrend(trend)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">{trend}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Clear Filters Button */}
      <button
        onClick={clearFilters}
        className="w-full py-2 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors font-medium text-sm"
      >
        Clear Filters
      </button>
    </aside>
  );
}

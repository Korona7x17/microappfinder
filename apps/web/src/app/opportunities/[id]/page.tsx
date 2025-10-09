/**
 * Opportunity Detail Page
 *
 * Shows full opportunity information:
 * - Title and summary
 * - All 6 dimensional scores (larger badges)
 * - Metadata (analyzed_at, confidence_level, enrichment info)
 * - Back to Browse link
 * - Dark mode support
 *
 * Note: This is a Server Component for better SEO
 */

import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { ScoreBadges } from '@/components/opportunities/ScoreBadges';
import { ThemeToggle } from '@/components/opportunities/ThemeToggle';

interface OpportunityDetailPageProps {
  params: {
    id: string;
  };
}

export default async function OpportunityDetailPage({ params }: OpportunityDetailPageProps) {
  let opportunity;

  try {
    opportunity = await api.opportunities.getById(params.id);
  } catch (error) {
    // If opportunity not found, show 404
    notFound();
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link
              href="/opportunities"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium text-sm inline-flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Browse
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <article className="bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-800 p-6 sm:p-8">
          {/* Title */}
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            {opportunity.title}
          </h1>

          {/* Summary */}
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">
            {opportunity.summary}
          </p>

          {/* Dimensional Scores */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Dimensional Scores
            </h2>
            <ScoreBadges opportunity={opportunity} />
          </div>

          {/* Confidence Level */}
          <div className="mb-8 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Analysis Confidence
              </span>
              <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {(opportunity.confidence_level * 100).toFixed(0)}%
              </span>
            </div>
            <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${opportunity.confidence_level * 100}%` }}
              />
            </div>
          </div>

          {/* Additional Details */}
          <div className="space-y-6">
            {/* Trend Data */}
            {opportunity.trend_data && opportunity.trend_data.timestamps.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Trend Analysis
                </h3>
                <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Data Points</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {opportunity.trend_data.timestamps.length}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-2">
                    <span className="text-gray-600 dark:text-gray-400">Growth Rate</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {(opportunity.trend_data.growth_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Geographic Spread */}
            {opportunity.geographic_spread && opportunity.geographic_spread.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Geographic Spread
                </h3>
                <div className="flex flex-wrap gap-2">
                  {opportunity.geographic_spread.map((region) => (
                    <span
                      key={region}
                      className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium"
                    >
                      {region}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Affected Industries */}
            {opportunity.affected_industries && opportunity.affected_industries.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Affected Industries
                </h3>
                <div className="flex flex-wrap gap-2">
                  {opportunity.affected_industries.map((industry) => (
                    <span
                      key={industry}
                      className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm font-medium"
                    >
                      {industry}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Metadata Footer */}
          <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-800">
            <div className="flex flex-wrap gap-4 text-sm text-gray-500 dark:text-gray-400">
              <div>
                <span className="font-medium">Source: </span>
                {opportunity.source_platform}
              </div>
              <div>
                <span className="font-medium">Analyzed: </span>
                {new Date(opportunity.analyzed_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </div>
              {opportunity.enrichment_count > 0 && (
                <div>
                  <span className="font-medium">Enriched: </span>
                  {opportunity.enrichment_count} {opportunity.enrichment_count === 1 ? 'time' : 'times'}
                </div>
              )}
              {opportunity.last_enriched_at && (
                <div>
                  <span className="font-medium">Last enriched: </span>
                  {new Date(opportunity.last_enriched_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })}
                </div>
              )}
            </div>
          </div>
        </article>
      </main>
    </div>
  );
}

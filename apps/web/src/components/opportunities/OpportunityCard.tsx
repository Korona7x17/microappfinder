/**
 * OpportunityCard Component
 *
 * Displays opportunity summary in a card format with:
 * - Title (truncated to 100 chars)
 * - Summary (truncated to 300 chars, 3 lines)
 * - All 6 dimensional score badges
 * - Click navigates to detail page
 * - Dark mode support
 */

'use client';

import Link from 'next/link';
import type { OpportunityListItem } from '@/types/opportunity';
import { ScoreBadges } from './ScoreBadges';

interface OpportunityCardProps {
  opportunity: OpportunityListItem;
}

export function OpportunityCard({ opportunity }: OpportunityCardProps) {
  return (
    <Link href={`/opportunities/${opportunity.id}`}>
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm hover:shadow-md hover:scale-105 transition-all duration-200 p-6 border border-gray-200 dark:border-gray-800 cursor-pointer">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2 line-clamp-2">
          {opportunity.title}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-3">
          {opportunity.summary}
        </p>
        <ScoreBadges opportunity={opportunity} />
      </div>
    </Link>
  );
}

# Implementation Tasks: Multi-Dimensional Opportunity Discovery Frontend

**Feature**: 003-multi-dimensional-opportunity | **Date**: 2025-10-09 | **Branch**: `003-multi-dimensional-opportunity`

## Overview

This document contains the ordered implementation tasks for building an IdeaBrowser-inspired discovery frontend with dark mode support. Tasks follow TDD (Test-Driven Development) order: write failing tests first, then implement functionality to make tests pass.

**Estimated Duration**: 16-20 hours (3-5 days)
**Constitution Compliance**: All principles validated in plan.md
**Frontend-Only**: No backend changes required (API already implemented)

## Task Dependencies

```
T001 (next-themes install) ━━┳━━ T003 (ThemeProvider setup)
T002 (TypeScript interfaces)  ┃
                               ┃
T003 ━━━━━━━━━━━━━━━━━━━━━━━━━╋━━ T004 (ThemeToggle component)
T005 (Tailwind dark config)   ┃
                               ┃
T006 (API client update) ━━━━━╋━━ T008 (useOpportunities hook)
T007 (Test: useOpportunities)  ┃
                               ┃
T009 (Test: OpportunityCard) ━━╋━━ T010 (OpportunityCard impl)
T011 (Test: ScoreBadges) ━━━━━╋━━ T012 (ScoreBadges impl)
T013 (Test: OpportunityGrid) ━╋━━ T014 (OpportunityGrid impl)
T015 (Test: FilterPanel) ━━━━━╋━━ T016 (FilterPanel impl)
T017 (Test: SortControls) ━━━━╋━━ T018 (SortControls impl)
                               ┃
T008, T010, T012, T014 ━━━━━━━╋━━ T019 (/opportunities page)
                               ┃
T008, T010 ━━━━━━━━━━━━━━━━━━━╋━━ T020 (/opportunities/[id] page)
                               ┃
T019 ━━━━━━━━━━━━━━━━━━━━━━━━━╋━━ T021 (Homepage redesign)
                               ┃
T021 ━━━━━━━━━━━━━━━━━━━━━━━━━╋━━ T022 (Responsive styles)
                               ┃
T022 ━━━━━━━━━━━━━━━━━━━━━━━━━╋━━ T023 (Theme testing)
                               ┃
T023 ━━━━━━━━━━━━━━━━━━━━━━━━━╋━━ T024 (Quickstart validation)
                               ┃
T024 ━━━━━━━━━━━━━━━━━━━━━━━━━┻━━ T025 (Performance testing)
```

## Tasks

### Phase 3.1: Setup & Dark Mode Foundation

---

### T001: Install next-themes Dependency

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 5min

**Objective**: Add next-themes library for dark mode support.

**Files**:
- Update: `apps/web/package.json`

**Command**:
```bash
cd apps/web && npm install next-themes
```

**Acceptance Criteria**:
- [ ] next-themes appears in package.json dependencies
- [ ] npm install runs without errors
- [ ] Version ~0.2.1 or later installed

**References**:
- plan.md:47 (next-themes dependency)
- research.md:364-379 (dark mode implementation)

---

### T002: Create TypeScript Interfaces

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 20min

**Objective**: Define TypeScript interfaces for opportunities, filters, and API responses.

**Files**:
- Create: `apps/web/src/types/opportunity.ts`

**Requirements**:
- Copy interfaces from plan.md:258-312
- Export all interfaces: `OpportunityListItem`, `OpportunityDetail`, `OpportunityFilters`, `SortField`, `SortOrder`, `OpportunitiesResponse`
- Add JSDoc comments for each interface
- Ensure strict TypeScript compliance (no `any` types)

**Acceptance Criteria**:
- [ ] File compiles without TypeScript errors
- [ ] All 6 dimensional scores typed correctly (severity 0-10, market_size enum, etc.)
- [ ] Enum types match backend contract (niche|mid|large, low|medium|high|saturated, etc.)

**References**:
- plan.md:258-312 (TypeScript interfaces)
- contracts/opportunity_api.yaml (API contract)

---

### T003: Configure ThemeProvider in Root Layout

**Priority**: High | **Dependencies**: T001 | **Estimated**: 15min

**Objective**: Wrap Next.js app with next-themes ThemeProvider for dark mode support.

**Files**:
- Update: `apps/web/src/app/layout.tsx`

**Requirements**:
- Import `ThemeProvider` from next-themes
- Wrap `{children}` with ThemeProvider
- Configuration: `attribute="class"`, `defaultTheme="system"`, `enableSystem={true}`
- Add `suppressHydrationWarning` to `<html>` tag (prevents flash)
- Preserve existing layout structure (metadata, fonts, etc.)

**Implementation**:
```tsx
import { ThemeProvider } from 'next-themes'

export default function RootLayout({ children }: { children: React.Node }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

**Acceptance Criteria**:
- [ ] App starts without hydration warnings
- [ ] System dark mode preference detected automatically
- [ ] Theme persists across page reloads (localStorage)

**References**:
- research.md:374-426 (ThemeProvider setup)
- plan.md:250-263 (dark mode implementation)

---

### T004: Create ThemeToggle Component

**Priority**: High | **Dependencies**: T003 | **Estimated**: 30min

**Objective**: Build toggle button for manual theme switching with sun/moon icons.

**Files**:
- Create: `apps/web/src/components/opportunities/ThemeToggle.tsx`

**Requirements**:
- Use `useTheme()` hook from next-themes
- Toggle between light/dark/system modes
- Display sun icon (light mode), moon icon (dark mode)
- Use shadcn/ui Button component for styling
- Add smooth transition animation (200ms)
- Keyboard accessible (Enter/Space to toggle)
- Include aria-label for accessibility

**Implementation Guide**:
```tsx
'use client'

import { useTheme } from 'next-themes'
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline' // or lucide-react

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="p-2 rounded-lg bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors"
      aria-label="Toggle theme"
    >
      {theme === 'dark' ? (
        <SunIcon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
      ) : (
        <MoonIcon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
      )}
    </button>
  )
}
```

**Acceptance Criteria**:
- [ ] Clicking toggles theme light ↔ dark
- [ ] Icon changes based on current theme
- [ ] Smooth transition animation
- [ ] Works with keyboard navigation
- [ ] No hydration mismatch warnings

**References**:
- research.md:405-442 (ThemeToggle component example)
- plan.md:151 (ThemeToggle in project structure)

---

### T005: Add Dark Mode Tailwind Configuration

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 10min

**Objective**: Enable Tailwind dark mode with class strategy.

**Files**:
- Update: `apps/web/tailwind.config.ts`

**Requirements**:
- Set `darkMode: 'class'` in config
- Ensure all color scales include dark variants
- Verify blue accent color contrast in dark mode

**Implementation**:
```typescript
const config = {
  darkMode: 'class', // Add this line
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // Existing theme extensions
    },
  },
  plugins: [],
}
```

**Acceptance Criteria**:
- [ ] Tailwind compiles without errors
- [ ] `dark:` variant works in components
- [ ] No build warnings related to dark mode

**References**:
- research.md:381-384 (Tailwind dark mode config)
- plan.md:258-263 (dark mode color system)

---

### Phase 3.2: API Integration & Data Fetching

---

### T006: Update API Client with Opportunities Methods

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 30min

**Objective**: Add opportunities API methods to existing API client.

**Files**:
- Update: `apps/web/src/lib/api.ts`

**Requirements**:
- Add `opportunities` namespace to API client
- Implement `listOpportunities(filters?, cursor?, limit?)` method
- Implement `getOpportunityById(id)` method
- Use existing axios instance/fetch pattern from file
- Type all methods with TypeScript interfaces from T002
- Handle query parameter serialization (filters → query string)

**Implementation Guide**:
```typescript
import type { OpportunityListItem, OpportunityDetail, OpportunityFilters, OpportunitiesResponse } from '@/types/opportunity'

export const api = {
  // ... existing methods ...

  opportunities: {
    async list(filters?: OpportunityFilters, cursor?: string, limit: number = 12): Promise<OpportunitiesResponse> {
      const params = new URLSearchParams()
      if (filters?.severity_min) params.set('severity_min', String(filters.severity_min))
      if (filters?.severity_max) params.set('severity_max', String(filters.severity_max))
      if (filters?.market_size) params.set('market_size', filters.market_size.join(','))
      // ... add all filter params
      if (cursor) params.set('cursor', cursor)
      params.set('limit', String(limit))

      const response = await fetch(`/api/opportunities?${params.toString()}`)
      if (!response.ok) throw new Error('Failed to fetch opportunities')
      return response.json()
    },

    async getById(id: string): Promise<OpportunityDetail> {
      const response = await fetch(`/api/opportunities/${id}`)
      if (!response.ok) throw new Error('Failed to fetch opportunity')
      return response.json()
    },
  },
}
```

**Acceptance Criteria**:
- [ ] Methods compile without TypeScript errors
- [ ] Query parameters serialize correctly
- [ ] Error handling works (network errors, 404s)
- [ ] Methods match existing API client pattern

**References**:
- plan.md:324-358 (API contracts)
- plan.md:154 (api.ts in project structure)

---

### T007: Write useOpportunities Hook Test

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 30min

**Objective**: Create TDD test for useOpportunities SWR hook (should FAIL initially).

**Files**:
- Create: `apps/web/tests/hooks/useOpportunities.test.ts`

**Requirements**:
- Test hook fetches initial data via SWR
- Test hook applies filters (updates query params)
- Test hook handles pagination (useSWRInfinite with cursor)
- Test loading states
- Test error states
- Mock API responses with msw or jest.fn()

**Test Cases**:
```typescript
describe('useOpportunities', () => {
  it('fetches initial opportunities on mount', async () => {
    // Should call api.opportunities.list()
    // Should return data, loading=false, error=null
  })

  it('applies filters and refetches', async () => {
    // Should include filter params in API call
    // Should update data when filters change
  })

  it('loads more opportunities with cursor', async () => {
    // Should call useSWRInfinite with cursor from previous page
    // Should append new opportunities to existing data
  })

  it('handles API errors gracefully', async () => {
    // Should set error state when API fails
    // Should not crash app
  })
})
```

**Acceptance Criteria**:
- [ ] All tests FAIL initially (hook not implemented yet)
- [ ] Tests use React Testing Library + SWR test utilities
- [ ] Tests are deterministic (no flakiness)
- [ ] Tests run in <5s

**References**:
- plan.md:367 (useOpportunities test requirement)
- research.md:279-299 (SWR pagination implementation)

---

### T008: Implement useOpportunities Hook (SWR Integration)

**Priority**: High | **Dependencies**: T006, T007 | **Estimated**: 1h

**Objective**: Build custom React hook for fetching opportunities with filters and pagination.

**Files**:
- Create: `apps/web/src/hooks/useOpportunities.ts`

**Requirements**:
- Use `useSWRInfinite` for cursor-based pagination
- Accept `filters` and `sortBy` parameters
- Return: `{ data, opportunities, error, isLoading, loadMore, hasMore }`
- Debounce filter changes (300ms) to prevent API spam
- Flatten paginated data into single opportunities array
- Cache with 5min stale-while-revalidate

**Implementation Guide**:
```typescript
'use client'

import useSWRInfinite from 'swr/infinite'
import type { OpportunityFilters, OpportunityListItem } from '@/types/opportunity'
import { api } from '@/lib/api'

export function useOpportunities(filters?: OpportunityFilters, sortBy = 'analyzed_at', sortOrder = 'desc') {
  const getKey = (pageIndex: number, previousPageData: any) => {
    if (previousPageData && !previousPageData.has_more) return null

    const cursor = pageIndex === 0 ? undefined : previousPageData?.next_cursor
    return ['opportunities', filters, sortBy, sortOrder, cursor]
  }

  const { data, error, size, setSize, isValidating } = useSWRInfinite(
    getKey,
    ([_, filters, sortBy, sortOrder, cursor]) =>
      api.opportunities.list(filters, cursor, 12),
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  )

  const opportunities: OpportunityListItem[] = data ? data.flatMap(page => page.opportunities) : []
  const hasMore = data?.[data.length - 1]?.has_more ?? false
  const isLoading = !data && !error

  const loadMore = () => setSize(size + 1)

  return {
    opportunities,
    error,
    isLoading,
    isValidating,
    loadMore,
    hasMore,
  }
}
```

**Acceptance Criteria**:
- [ ] Hook fetches opportunities successfully
- [ ] Filters update query params correctly
- [ ] Pagination appends new pages (doesn't replace)
- [ ] Debouncing prevents API spam
- [ ] T007 tests now PASS
- [ ] No memory leaks on unmount

**References**:
- research.md:279-299 (SWR pagination strategy)
- plan.md:431 (useOpportunities hook implementation)

---

### Phase 3.3: Component Tests (TDD)

---

### T009: Write OpportunityCard Component Test

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 20min

**Objective**: Create TDD test for OpportunityCard component (should FAIL initially).

**Files**:
- Create: `apps/web/tests/components/opportunities/OpportunityCard.test.tsx`

**Requirements**:
- Test renders opportunity title and summary
- Test displays all 6 score badges
- Test handles click event (navigation)
- Test dark mode classes applied correctly
- Mock opportunity data with full interface

**Test Cases**:
```typescript
describe('OpportunityCard', () => {
  const mockOpportunity: OpportunityListItem = {
    id: 'test-id',
    title: 'Test Opportunity',
    summary: 'Test summary',
    problem_severity: 8.5,
    market_size: 'large',
    monetization_potential: 7.0,
    technical_complexity: 5.0,
    competition_level: 'medium',
    trend_direction: 'growing',
    confidence_level: 0.85,
    analyzed_at: '2025-10-09T12:00:00Z',
  }

  it('renders title and summary', () => {
    render(<OpportunityCard opportunity={mockOpportunity} />)
    expect(screen.getByText('Test Opportunity')).toBeInTheDocument()
  })

  it('displays all 6 score badges', () => {
    // Check for severity, market size, monetization, complexity, competition, trend
  })

  it('navigates on click', () => {
    // Verify router.push or Link component
  })
})
```

**Acceptance Criteria**:
- [ ] All tests FAIL initially (component not implemented yet)
- [ ] Tests use React Testing Library
- [ ] Tests are deterministic
- [ ] Tests run in <3s

**References**:
- plan.md:363 (OpportunityCard test requirement)

---

### T010: Implement OpportunityCard Component with Dark Mode

**Priority**: High | **Dependencies**: T002, T009 | **Estimated**: 45min

**Objective**: Build card component for displaying opportunity summary with all scores.

**Files**:
- Create: `apps/web/src/components/opportunities/OpportunityCard.tsx`

**Requirements**:
- Display: title (first 100 chars), summary (first 300 chars)
- Show all 6 score badges in a responsive grid
- Card hover effect (scale-105, shadow increase)
- Click navigates to `/opportunities/[id]`
- Dark mode: bg-white → dark:bg-gray-900, text adjustments
- Rounded corners (rounded-lg), subtle shadow (shadow-sm)

**Implementation Guide**:
```tsx
'use client'

import Link from 'next/link'
import type { OpportunityListItem } from '@/types/opportunity'
import { ScoreBadges } from './ScoreBadges'

export function OpportunityCard({ opportunity }: { opportunity: OpportunityListItem }) {
  return (
    <Link href={`/opportunities/${opportunity.id}`}>
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm hover:shadow-md hover:scale-105 transition-all duration-200 p-6 border border-gray-200 dark:border-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          {opportunity.title}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-3">
          {opportunity.summary}
        </p>
        <ScoreBadges opportunity={opportunity} />
      </div>
    </Link>
  )
}
```

**Acceptance Criteria**:
- [ ] Card renders with correct styling
- [ ] Hover effect works smoothly
- [ ] Click navigates to detail page
- [ ] Dark mode styles applied correctly
- [ ] T009 tests now PASS

**References**:
- plan.md:186-196 (card-based design)
- research.md:387-403 (color system light/dark)

---

### T011: Write ScoreBadges Component Test

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 15min

**Objective**: Create TDD test for ScoreBadges component (should FAIL initially).

**Files**:
- Create: `apps/web/tests/components/opportunities/ScoreBadges.test.tsx`

**Requirements**:
- Test renders all 6 score badges
- Test color-coding based on score values (severity: red high, green low)
- Test dark mode badge colors

**Test Cases**:
```typescript
describe('ScoreBadges', () => {
  it('renders severity badge with correct color', () => {
    // High severity (8+) → red, Low (0-4) → green
  })

  it('renders market size badge', () => {
    // niche → yellow, mid → blue, large → purple
  })

  it('renders all 6 badges', () => {
    // Verify 6 badge elements exist
  })
})
```

**Acceptance Criteria**:
- [ ] All tests FAIL initially
- [ ] Tests cover all 6 score types
- [ ] Tests run in <2s

---

### T012: Implement ScoreBadges Component with Dark Mode

**Priority**: High | **Dependencies**: T002, T011 | **Estimated**: 30min

**Objective**: Build badge component for displaying 6-dimensional scores.

**Files**:
- Create: `apps/web/src/components/opportunities/ScoreBadges.tsx`

**Requirements**:
- Display all 6 scores as color-coded badges
- Color mapping:
  - Severity: bg-red-100 (high), bg-green-100 (low)
  - Market Size: bg-purple-100 (large), bg-yellow-100 (niche)
  - Monetization: bg-green-100
  - Complexity: bg-orange-100
  - Competition: bg-yellow-100
  - Trend: bg-blue-100
- Dark mode: Adjust background opacity for readability
- Responsive grid layout (2 cols mobile, 3 cols desktop)

**Implementation Guide**:
```tsx
import type { OpportunityListItem } from '@/types/opportunity'

export function ScoreBadges({ opportunity }: { opportunity: OpportunityListItem }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
      <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-xs font-medium">
        Severity: {opportunity.problem_severity.toFixed(1)}
      </span>
      <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs font-medium">
        {opportunity.market_size} market
      </span>
      {/* Add remaining 4 badges */}
    </div>
  )
}
```

**Acceptance Criteria**:
- [ ] All 6 badges render correctly
- [ ] Colors match specification
- [ ] Dark mode badges readable
- [ ] Responsive layout works
- [ ] T011 tests now PASS

**References**:
- research.md:400-402 (score badge colors)

---

### T013: Write OpportunityGrid Component Test

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 20min

**Objective**: Create TDD test for OpportunityGrid component (should FAIL initially).

**Files**:
- Create: `apps/web/tests/components/opportunities/OpportunityGrid.test.tsx`

**Requirements**:
- Test renders grid of OpportunityCard components
- Test empty state when no opportunities
- Test loading state (skeleton loaders)
- Test "Load More" button functionality

**Test Cases**:
```typescript
describe('OpportunityGrid', () => {
  it('renders grid with opportunity cards', () => {
    const mockOpportunities = [/* array of 12 items */]
    render(<OpportunityGrid opportunities={mockOpportunities} />)
    expect(screen.getAllByRole('link')).toHaveLength(12)
  })

  it('shows empty state when no opportunities', () => {
    render(<OpportunityGrid opportunities={[]} />)
    expect(screen.getByText(/no opportunities/i)).toBeInTheDocument()
  })

  it('shows skeleton loaders when loading', () => {
    render(<OpportunityGrid isLoading={true} />)
    // Check for skeleton elements
  })
})
```

**Acceptance Criteria**:
- [ ] All tests FAIL initially
- [ ] Tests cover all states (loading/empty/populated)
- [ ] Tests run in <3s

---

### T014: Implement OpportunityGrid Component with Dark Mode

**Priority**: High | **Dependencies**: T010, T012, T013 | **Estimated**: 45min

**Objective**: Build grid container for opportunity cards with responsive layout.

**Files**:
- Create: `apps/web/src/components/opportunities/OpportunityGrid.tsx`

**Requirements**:
- Responsive grid: 1 col (mobile), 2 col (tablet), 3 col (desktop)
- Render OpportunityCard for each opportunity
- Empty state: "No opportunities match your filters" + reset button
- Loading state: 12 skeleton loaders (animate-pulse)
- "Load More" button at bottom (if hasMore)

**Implementation Guide**:
```tsx
import { OpportunityCard } from './OpportunityCard'
import type { OpportunityListItem } from '@/types/opportunity'

interface OpportunityGridProps {
  opportunities: OpportunityListItem[]
  isLoading?: boolean
  hasMore?: boolean
  onLoadMore?: () => void
}

export function OpportunityGrid({ opportunities, isLoading, hasMore, onLoadMore }: OpportunityGridProps) {
  if (isLoading && opportunities.length === 0) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="h-64 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (opportunities.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">No opportunities match your filters.</p>
      </div>
    )
  }

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {opportunities.map(opp => (
          <OpportunityCard key={opp.id} opportunity={opp} />
        ))}
      </div>
      {hasMore && (
        <div className="text-center mt-8">
          <button onClick={onLoadMore} className="px-6 py-3 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600">
            Load More
          </button>
        </div>
      )}
    </>
  )
}
```

**Acceptance Criteria**:
- [ ] Grid responsive at all breakpoints
- [ ] Empty state displays correctly
- [ ] Skeleton loaders show during initial load
- [ ] "Load More" button works
- [ ] T013 tests now PASS

**References**:
- plan.md:230-237 (responsive breakpoints)
- research.md:310-315 (skeleton loaders)

---

### T015: Write FilterPanel Component Test

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 25min

**Objective**: Create TDD test for FilterPanel component (should FAIL initially).

**Files**:
- Create: `apps/web/tests/components/opportunities/FilterPanel.test.tsx`

**Requirements**:
- Test renders all 6 filter types (3 sliders, 3 multi-selects)
- Test slider changes update filter state
- Test checkbox selection updates filter state
- Test "Clear Filters" button resets all

**Test Cases**:
```typescript
describe('FilterPanel', () => {
  it('renders all filter controls', () => {
    // Check for severity slider, market size checkboxes, etc.
  })

  it('updates filters on slider change', async () => {
    const onFilterChange = jest.fn()
    render(<FilterPanel onFilterChange={onFilterChange} />)
    // Simulate slider drag
    // Expect onFilterChange called with new values
  })

  it('clears all filters on button click', () => {
    // Set some filters, click clear, verify all reset
  })
})
```

**Acceptance Criteria**:
- [ ] All tests FAIL initially
- [ ] Tests cover all 6 filter types
- [ ] Tests verify debouncing (300ms delay)
- [ ] Tests run in <5s

---

### T016: Implement FilterPanel Component with Dark Mode

**Priority**: High | **Dependencies**: T002, T015 | **Estimated**: 1.5h

**Objective**: Build side panel with 6 filter types (sliders + multi-selects).

**Files**:
- Create: `apps/web/src/components/opportunities/FilterPanel.tsx`

**Requirements**:
- 3 range sliders: Severity (0-10), Monetization (0-10), Complexity (0-10)
- 3 multi-select checkboxes: Market Size, Competition, Trend
- Debounce slider changes (300ms)
- "Clear Filters" button at bottom
- Dark mode: bg-white → dark:bg-gray-900
- Collapsible sections for mobile

**Implementation Guide**:
```tsx
'use client'

import { useState, useEffect } from 'react'
import { useDebounce } from '@/hooks/useDebounce'
import type { OpportunityFilters } from '@/types/opportunity'

export function FilterPanel({ onFilterChange }: { onFilterChange: (filters: OpportunityFilters) => void }) {
  const [filters, setFilters] = useState<OpportunityFilters>({})
  const debouncedFilters = useDebounce(filters, 300)

  useEffect(() => {
    onFilterChange(debouncedFilters)
  }, [debouncedFilters, onFilterChange])

  const updateSeverity = (min: number, max: number) => {
    setFilters(prev => ({ ...prev, severity_min: min, severity_max: max }))
  }

  const toggleMarketSize = (size: 'niche' | 'mid' | 'large') => {
    setFilters(prev => {
      const current = prev.market_size || []
      return {
        ...prev,
        market_size: current.includes(size)
          ? current.filter(s => s !== size)
          : [...current, size]
      }
    })
  }

  const clearFilters = () => setFilters({})

  return (
    <aside className="w-64 bg-white dark:bg-gray-900 rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">Filters</h2>

      {/* Severity Range Slider (use shadcn/ui Slider component) */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Problem Severity</label>
        {/* Dual-handle slider component */}
      </div>

      {/* Market Size Multi-Select */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Market Size</label>
        <div className="space-y-2">
          <label className="flex items-center">
            <input type="checkbox" onChange={() => toggleMarketSize('niche')} />
            <span className="ml-2">Niche</span>
          </label>
          {/* Add mid, large */}
        </div>
      </div>

      {/* Add remaining filters... */}

      <button onClick={clearFilters} className="w-full py-2 bg-gray-200 dark:bg-gray-800 rounded hover:bg-gray-300 dark:hover:bg-gray-700">
        Clear Filters
      </button>
    </aside>
  )
}
```

**Acceptance Criteria**:
- [ ] All 6 filters functional
- [ ] Debouncing works (no API spam)
- [ ] Clear button resets everything
- [ ] Dark mode styles applied
- [ ] T015 tests now PASS

**References**:
- plan.md:198-208 (filter UX requirements)
- research.md:260-274 (filter types)

---

### T017: Write SortControls Component Test

**Priority**: High | **Parallelizable**: Yes | **Estimated**: 15min

**Objective**: Create TDD test for SortControls component (should FAIL initially).

**Files**:
- Create: `apps/web/tests/components/opportunities/SortControls.test.tsx`

**Requirements**:
- Test renders sort dropdown with 4 options
- Test changing sort field triggers callback
- Test toggling sort order (ASC ↔ DESC)

**Test Cases**:
```typescript
describe('SortControls', () => {
  it('renders sort dropdown', () => {
    render(<SortControls onSortChange={jest.fn()} />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('calls callback when sort field changes', () => {
    const onSortChange = jest.fn()
    // Select "Monetization", verify callback called
  })

  it('toggles sort order', () => {
    // Click order toggle button, verify ASC → DESC
  })
})
```

**Acceptance Criteria**:
- [ ] All tests FAIL initially
- [ ] Tests run in <2s

---

### T018: Implement SortControls Component with Dark Mode

**Priority**: High | **Dependencies**: T002, T017 | **Estimated**: 30min

**Objective**: Build dropdown for sorting opportunities by any dimension.

**Files**:
- Create: `apps/web/src/components/opportunities/SortControls.tsx`

**Requirements**:
- Dropdown with 4 options: Severity, Monetization, Analyzed At, Complexity
- Sort order toggle button (↑ ASC, ↓ DESC)
- Use shadcn/ui Select component
- Default: Analyzed At DESC
- Dark mode styling

**Implementation Guide**:
```tsx
'use client'

import { useState } from 'react'
import type { SortField, SortOrder } from '@/types/opportunity'

export function SortControls({ onSortChange }: { onSortChange: (field: SortField, order: SortOrder) => void }) {
  const [sortField, setSortField] = useState<SortField>('analyzed_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  const handleFieldChange = (field: SortField) => {
    setSortField(field)
    onSortChange(field, sortOrder)
  }

  const toggleOrder = () => {
    const newOrder = sortOrder === 'asc' ? 'desc' : 'asc'
    setSortOrder(newOrder)
    onSortChange(sortField, newOrder)
  }

  return (
    <div className="flex items-center gap-2">
      <select
        value={sortField}
        onChange={(e) => handleFieldChange(e.target.value as SortField)}
        className="px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded"
      >
        <option value="analyzed_at">Latest</option>
        <option value="severity">Severity</option>
        <option value="monetization">Monetization</option>
        <option value="complexity">Complexity</option>
      </select>
      <button onClick={toggleOrder} className="px-3 py-2 bg-gray-200 dark:bg-gray-800 rounded">
        {sortOrder === 'asc' ? '↑' : '↓'}
      </button>
    </div>
  )
}
```

**Acceptance Criteria**:
- [ ] Dropdown shows all 4 options
- [ ] Sort order toggles correctly
- [ ] Callback fires with correct values
- [ ] Dark mode styles applied
- [ ] T017 tests now PASS

**References**:
- plan.md:269 (sort dropdown)

---

### Phase 3.4: Routes & Pages

---

### T019: Create /opportunities Page Route with ThemeToggle

**Priority**: High | **Dependencies**: T004, T008, T014, T016, T018 | **Estimated**: 1h

**Objective**: Build main opportunities browsing page with filters, grid, and theme toggle.

**Files**:
- Create: `apps/web/src/app/opportunities/page.tsx`

**Requirements**:
- Use `useOpportunities` hook with URL-based filter state
- Render FilterPanel (sidebar desktop, bottom sheet mobile)
- Render SortControls in header
- Render OpportunityGrid with fetched opportunities
- Add ThemeToggle in top-right corner
- Client component ('use client')
- Dark mode: bg-gray-50 → dark:bg-gray-950

**Implementation Guide**:
```tsx
'use client'

import { useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useOpportunities } from '@/hooks/useOpportunities'
import { OpportunityGrid } from '@/components/opportunities/OpportunityGrid'
import { FilterPanel } from '@/components/opportunities/FilterPanel'
import { SortControls } from '@/components/opportunities/SortControls'
import { ThemeToggle } from '@/components/opportunities/ThemeToggle'

export default function OpportunitiesPage() {
  const searchParams = useSearchParams()
  const router = useRouter()

  // Parse filters from URL
  const filters = {
    severity_min: searchParams.get('severity_min') ? Number(searchParams.get('severity_min')) : undefined,
    // ... parse all filters
  }

  const { opportunities, isLoading, hasMore, loadMore } = useOpportunities(filters)

  const handleFilterChange = (newFilters: OpportunityFilters) => {
    const params = new URLSearchParams()
    // Build params from newFilters
    router.push(`/opportunities?${params.toString()}`)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Discover Opportunities</h1>
          <div className="flex items-center gap-4">
            <SortControls onSortChange={/* ... */} />
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex gap-8">
          <FilterPanel onFilterChange={handleFilterChange} />
          <div className="flex-1">
            <OpportunityGrid
              opportunities={opportunities}
              isLoading={isLoading}
              hasMore={hasMore}
              onLoadMore={loadMore}
            />
          </div>
        </div>
      </main>
    </div>
  )
}
```

**Acceptance Criteria**:
- [ ] Page renders with all components
- [ ] Filters update URL params
- [ ] Grid displays opportunities
- [ ] Theme toggle works
- [ ] Responsive layout (sidebar collapses on mobile)
- [ ] Dark mode styles applied throughout

**References**:
- plan.md:137-139 (opportunities page route)
- research.md:330-353 (URL-based state)

---

### T020: Create /opportunities/[id] Detail Page Route with Dark Mode

**Priority**: High | **Dependencies**: T008, T010 | **Estimated**: 1h

**Objective**: Build opportunity detail page showing full information including trend data.

**Files**:
- Create: `apps/web/src/app/opportunities/[id]/page.tsx`

**Requirements**:
- Fetch full opportunity details using `api.opportunities.getById(id)`
- Display all 6 dimensional scores (larger badges)
- Show trend_data as line chart (use recharts or similar)
- Display geographic_spread as tag list
- Display affected_industries as tag list
- Show enrichment metadata (enrichment_count, last_enriched_at)
- Add "Back to Browse" link
- Dark mode: match opportunities page styling

**Implementation Guide**:
```tsx
import { api } from '@/lib/api'
import { ScoreBadges } from '@/components/opportunities/ScoreBadges'
import Link from 'next/link'

export default async function OpportunityDetailPage({ params }: { params: { id: string } }) {
  const opportunity = await api.opportunities.getById(params.id)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Link href="/opportunities" className="text-blue-600 dark:text-blue-400 hover:underline mb-4 inline-block">
          ← Back to Browse
        </Link>

        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold mb-4 text-gray-900 dark:text-gray-100">
            {opportunity.title}
          </h1>

          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {opportunity.summary}
          </p>

          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-3">Dimensional Scores</h2>
            <ScoreBadges opportunity={opportunity} />
          </div>

          {/* Add trend chart, geographies, industries */}

          <div className="text-sm text-gray-500 dark:text-gray-400">
            Analyzed: {new Date(opportunity.analyzed_at).toLocaleDateString()}
            {opportunity.enrichment_count > 0 && (
              <span className="ml-4">Enriched {opportunity.enrichment_count} times</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
```

**Acceptance Criteria**:
- [ ] Page fetches and displays opportunity details
- [ ] All 6 scores visible
- [ ] Metadata displayed correctly
- [ ] Back link works
- [ ] Dark mode styles applied
- [ ] 404 handling for invalid IDs

**References**:
- plan.md:138-140 (detail page route)
- plan.md:293-305 (OpportunityDetail interface)

---

### T021: Redesign Homepage with Dark Mode Support

**Priority**: High | **Dependencies**: T019 | **Estimated**: 45min

**Objective**: Transform homepage into discovery landing page with link to /opportunities.

**Files**:
- Update: `apps/web/src/app/page.tsx`

**Requirements**:
- Replace existing landing with discovery-focused design
- Prominent CTA button → "Discover Opportunities"
- Add ThemeToggle in header
- Brief description of platform
- Keep existing auth links for registered users
- Dark mode: bg-gray-50 → dark:bg-gray-950

**Implementation Guide**:
```tsx
import Link from 'next/link'
import { ThemeToggle } from '@/components/opportunities/ThemeToggle'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">MicroAppFinder</h1>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100">
              Dashboard
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-24 text-center">
        <h2 className="text-5xl font-bold text-gray-900 dark:text-gray-100 mb-6">
          Discover Validated Micro-App Opportunities
        </h2>
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-12">
          Browse a curated catalog of business opportunities with 6-dimensional scoring—from Reddit & HackerNews pain points.
        </p>
        <Link
          href="/opportunities"
          className="px-8 py-4 bg-blue-600 dark:bg-blue-500 text-white rounded-lg text-lg font-medium hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors inline-block"
        >
          Explore Opportunities →
        </Link>
      </main>
    </div>
  )
}
```

**Acceptance Criteria**:
- [ ] Homepage loads with new design
- [ ] CTA button links to /opportunities
- [ ] ThemeToggle works
- [ ] Dark mode styles applied
- [ ] Existing dashboard link preserved

**References**:
- plan.md:31 (discovery-first platform goal)
- plan.md:136 (homepage in project structure)

---

### T022: Add Responsive Styles & Mobile Optimization

**Priority**: High | **Dependencies**: T021 | **Estimated**: 1h

**Objective**: Ensure all pages work perfectly on mobile/tablet/desktop with dark mode.

**Files**:
- Review all components created in T010-T021
- Add/fix responsive Tailwind classes

**Requirements**:
- Mobile (< 640px): Single column grid, bottom sheet filters, stacked layout
- Tablet (640-1024px): 2-column grid, collapsible filters
- Desktop (1024px+): 3-column grid, persistent filters
- Test filter panel on mobile (use shadcn/ui Sheet component)
- Verify touch targets ≥44px (iOS guidelines)
- Test dark mode on all breakpoints

**Implementation Checklist**:
```
- [ ] OpportunityGrid: grid-cols-1 sm:grid-cols-2 lg:grid-cols-3
- [ ] FilterPanel: Hidden on mobile, Sheet component overlay
- [ ] OpportunityCard: Touch-friendly click area
- [ ] SortControls: Compact on mobile
- [ ] Homepage: Responsive padding and text sizes
- [ ] Detail page: Single column on mobile
```

**Testing**:
- Use Chrome DevTools responsive mode
- Test on iPhone SE (375px), iPad (768px), Desktop (1440px)
- Verify no horizontal scroll
- Check dark mode contrast on all breakpoints

**Acceptance Criteria**:
- [ ] All pages responsive at 3 breakpoints
- [ ] No layout shifts or overflow
- [ ] Dark mode readable on all devices
- [ ] Touch targets appropriate size

**References**:
- plan.md:230-237 (responsive breakpoints)
- research.md:232-236 (mobile-first approach)

---

### Phase 3.5: Testing & Validation

---

### T023: Test Theme Persistence & System Preference Detection

**Priority**: High | **Dependencies**: T022 | **Estimated**: 30min

**Objective**: Verify dark mode works correctly across all scenarios.

**Test Scenarios**:
1. System preference detection:
   - Set OS to dark mode → App starts in dark mode
   - Set OS to light mode → App starts in light mode

2. Manual toggle persistence:
   - Toggle to dark → Reload page → Still dark
   - Toggle to light → Reload page → Still light

3. No flash of unstyled content:
   - Hard refresh → No white flash in dark mode
   - Verify `suppressHydrationWarning` works

4. Cross-browser testing:
   - Test on Chrome, Firefox, Safari
   - Verify localStorage works in all browsers

**Validation Checklist**:
```
- [ ] System dark mode auto-detected
- [ ] Manual toggle persists across reloads
- [ ] No hydration warnings in console
- [ ] No FOUC (flash of unstyled content)
- [ ] Theme syncs across tabs (test localStorage events)
- [ ] Works in incognito mode (with localStorage)
```

**Acceptance Criteria**:
- [ ] All 6 test scenarios pass
- [ ] No console errors related to theme
- [ ] Smooth theme transitions (<200ms)

**References**:
- research.md:451-456 (dark mode testing checklist)

---

### T024: Run Quickstart Validation

**Priority**: High | **Dependencies**: T023 | **Estimated**: 30min

**Objective**: Execute full user flow from quickstart.md to verify feature completeness.

**Validation Flow**:
1. Visit homepage → See discovery landing page
2. Click "Explore Opportunities" → Navigate to /opportunities
3. See opportunity grid with 12 results
4. Apply filter (severity ≥7) → Grid updates instantly (debounced)
5. Sort by monetization DESC → Highest monetization opportunities first
6. Toggle dark mode → Theme switches without page reload
7. Click opportunity card → Navigate to detail page
8. View full opportunity details → See all 6 scores + metadata
9. Click "Back to Browse" → Return to /opportunities (filters preserved)
10. Click "Load More" → Fetch next page (cursor pagination)
11. Hard refresh → Theme persists, filters preserved in URL

**Success Criteria**:
- [ ] All 11 steps complete without errors
- [ ] No console warnings or errors
- [ ] Performance feels smooth (<500ms API response)
- [ ] Dark mode works throughout flow
- [ ] URL updates correctly with filters

**Documentation**:
- Record any issues or unexpected behavior
- Take screenshots of key pages (light + dark mode)
- Note any performance concerns

**References**:
- plan.md:389-395 (quickstart user flow)

---

### T025: Performance Testing & Optimization

**Priority**: High | **Dependencies**: T024 | **Estimated**: 1h

**Objective**: Verify performance targets met and optimize if needed.

**Performance Targets** (from plan.md):
- API response: <500ms p95
- Page load: <1s First Contentful Paint
- Animations: 60fps (smooth)
- Theme toggle: <200ms

**Testing Tools**:
- Lighthouse CI (Chrome DevTools)
- Web Vitals monitoring
- Network tab for API timing
- Performance profiler for animations

**Test Scenarios**:
1. **Initial page load** (/opportunities):
   - Measure FCP, LCP, CLS
   - Target: Lighthouse score >90

2. **API response time**:
   - Measure GET /api/opportunities with filters
   - Target: p95 <500ms

3. **Filter interaction**:
   - Measure time from slider change → grid update
   - Target: <300ms debounce + <500ms API = <800ms total

4. **Theme toggle**:
   - Measure visual transition time
   - Target: <200ms

5. **Pagination**:
   - Measure "Load More" button → new cards visible
   - Target: <500ms

**Optimization Checklist**:
```
- [ ] Bundle size <500KB (check with `npm run build`)
- [ ] Images lazy loaded (if any)
- [ ] SWR caching working (check Network tab)
- [ ] No unnecessary re-renders (React DevTools Profiler)
- [ ] Debouncing prevents API spam
- [ ] Skeleton loaders reduce perceived load time
```

**Acceptance Criteria**:
- [ ] All performance targets met
- [ ] Lighthouse score >90 (Performance)
- [ ] No layout shifts (CLS <0.1)
- [ ] Smooth 60fps animations

**References**:
- plan.md:52-53 (performance goals)
- research.md:307-325 (performance optimization strategy)

---

## Completion Checklist

**Phase Status**:
- [ ] Phase 3.1: Setup complete (T001-T005)
- [ ] Phase 3.2: API integration complete (T006-T008)
- [ ] Phase 3.3: Component tests complete (T009-T018)
- [ ] Phase 3.4: Routes complete (T019-T022)
- [ ] Phase 3.5: Validation complete (T023-T025)

**Deliverables**:
- [ ] Dark mode fully functional (light + dark + system preference)
- [ ] All 7 components implemented and tested
- [ ] 3 routes created (/opportunities, /opportunities/[id], /)
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] All quickstart scenarios pass
- [ ] Performance targets met

**Ready for Production**:
- [ ] Branch: `003-multi-dimensional-opportunity`
- [ ] All tests passing (unit + component)
- [ ] No TypeScript errors
- [ ] No console warnings in production build
- [ ] Lighthouse score >90
- [ ] Dark mode tested across browsers

---

## Parallel Execution Examples

**Setup Phase (can run together)**:
```bash
# T001 + T002 + T005 in parallel
Task: "Install next-themes dependency"
Task: "Create TypeScript interfaces in apps/web/src/types/opportunity.ts"
Task: "Add dark mode Tailwind configuration in apps/web/tailwind.config.ts"
```

**Component Tests (can run together)**:
```bash
# T009 + T011 + T013 + T015 + T017 in parallel
Task: "Write OpportunityCard component test"
Task: "Write ScoreBadges component test"
Task: "Write OpportunityGrid component test"
Task: "Write FilterPanel component test"
Task: "Write SortControls component test"
```

**Component Implementation (after tests, can run some in parallel)**:
```bash
# T010 + T012 in parallel (different files)
Task: "Implement OpportunityCard component"
Task: "Implement ScoreBadges component"
```

---

**Estimated Total Duration**: 16-20 hours (3-5 days)
**Based on**: plan.md Phase 2 task planning approach with TDD methodology

**Note**: Dark mode adds ~3-4 hours to original 18-task estimate. Responsive design and performance testing are critical for production readiness.

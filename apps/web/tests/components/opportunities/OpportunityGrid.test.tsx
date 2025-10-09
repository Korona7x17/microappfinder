/**
 * Test: OpportunityGrid Component
 * Tests the grid container for opportunity cards with loading/empty states
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { OpportunityGrid } from '@/components/opportunities/OpportunityGrid';
import type { OpportunityListItem } from '@/types/opportunity';

// Mock OpportunityCard component
jest.mock('@/components/opportunities/OpportunityCard', () => ({
  OpportunityCard: ({ opportunity }: { opportunity: OpportunityListItem }) => (
    <div data-testid={`opportunity-card-${opportunity.id}`}>{opportunity.title}</div>
  ),
}));

describe('OpportunityGrid', () => {
  const mockOpportunities: OpportunityListItem[] = [
    {
      id: 'opp-1',
      title: 'Opportunity 1',
      summary: 'Summary 1',
      problem_severity: 8.0,
      market_size: 'large',
      monetization_potential: 7.0,
      technical_complexity: 5.0,
      competition_level: 'medium',
      trend_direction: 'growing',
      confidence_level: 0.85,
      analyzed_at: '2025-10-09T12:00:00Z',
    },
    {
      id: 'opp-2',
      title: 'Opportunity 2',
      summary: 'Summary 2',
      problem_severity: 7.5,
      market_size: 'mid',
      monetization_potential: 6.5,
      technical_complexity: 4.0,
      competition_level: 'low',
      trend_direction: 'explosive',
      confidence_level: 0.90,
      analyzed_at: '2025-10-09T11:00:00Z',
    },
    {
      id: 'opp-3',
      title: 'Opportunity 3',
      summary: 'Summary 3',
      problem_severity: 9.0,
      market_size: 'large',
      monetization_potential: 8.5,
      technical_complexity: 6.0,
      competition_level: 'high',
      trend_direction: 'growing',
      confidence_level: 0.80,
      analyzed_at: '2025-10-09T10:00:00Z',
    },
  ];

  it('renders grid with opportunity cards', () => {
    render(<OpportunityGrid opportunities={mockOpportunities} />);

    expect(screen.getByTestId('opportunity-card-opp-1')).toBeInTheDocument();
    expect(screen.getByTestId('opportunity-card-opp-2')).toBeInTheDocument();
    expect(screen.getByTestId('opportunity-card-opp-3')).toBeInTheDocument();
  });

  it('renders correct number of cards', () => {
    render(<OpportunityGrid opportunities={mockOpportunities} />);

    const cards = screen.getAllByTestId(/opportunity-card/);
    expect(cards).toHaveLength(3);
  });

  it('shows empty state when no opportunities', () => {
    render(<OpportunityGrid opportunities={[]} />);

    expect(screen.getByText(/no opportunities match your filters/i)).toBeInTheDocument();
  });

  it('shows skeleton loaders when loading', () => {
    const { container } = render(<OpportunityGrid opportunities={[]} isLoading={true} />);

    // Should show 12 skeleton loaders
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(12);
  });

  it('does not show skeletons when loading with existing data', () => {
    const { container } = render(
      <OpportunityGrid opportunities={mockOpportunities} isLoading={true} />
    );

    // Should show cards, not skeletons, when paginating
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(0);

    expect(screen.getByTestId('opportunity-card-opp-1')).toBeInTheDocument();
  });

  it('shows "Load More" button when hasMore is true', () => {
    render(<OpportunityGrid opportunities={mockOpportunities} hasMore={true} />);

    expect(screen.getByText('Load More')).toBeInTheDocument();
  });

  it('does not show "Load More" button when hasMore is false', () => {
    render(<OpportunityGrid opportunities={mockOpportunities} hasMore={false} />);

    expect(screen.queryByText('Load More')).not.toBeInTheDocument();
  });

  it('calls onLoadMore when "Load More" button is clicked', () => {
    const onLoadMore = jest.fn();

    render(
      <OpportunityGrid
        opportunities={mockOpportunities}
        hasMore={true}
        onLoadMore={onLoadMore}
      />
    );

    const loadMoreButton = screen.getByText('Load More');
    fireEvent.click(loadMoreButton);

    expect(onLoadMore).toHaveBeenCalledTimes(1);
  });

  it('applies responsive grid layout', () => {
    const { container } = render(<OpportunityGrid opportunities={mockOpportunities} />);

    // Check for responsive grid classes
    const grid = container.querySelector('.grid-cols-1');
    expect(grid).toBeInTheDocument();

    const smGrid = container.querySelector('.sm\\:grid-cols-2');
    expect(smGrid).toBeInTheDocument();

    const lgGrid = container.querySelector('.lg\\:grid-cols-3');
    expect(lgGrid).toBeInTheDocument();
  });

  it('applies dark mode classes to Load More button', () => {
    const { container } = render(
      <OpportunityGrid opportunities={mockOpportunities} hasMore={true} />
    );

    const button = container.querySelector('.dark\\:bg-blue-500');
    expect(button).toBeInTheDocument();
  });

  it('applies dark mode classes to empty state', () => {
    const { container} = render(<OpportunityGrid opportunities={[]} />);

    const emptyText = container.querySelector('.dark\\:text-gray-400');
    expect(emptyText).toBeInTheDocument();
  });

  it('applies dark mode classes to skeleton loaders', () => {
    const { container } = render(<OpportunityGrid opportunities={[]} isLoading={true} />);

    const darkSkeleton = container.querySelector('.dark\\:bg-gray-800');
    expect(darkSkeleton).toBeInTheDocument();
  });
});

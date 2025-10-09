/**
 * Test: OpportunityCard Component
 * TDD approach - these tests should FAIL initially
 *
 * Tests the card component for displaying opportunity summaries
 */

import { render, screen } from '@testing-library/react';
import { OpportunityCard } from '@/components/opportunities/OpportunityCard';
import type { OpportunityListItem } from '@/types/opportunity';

// Mock Next.js Link component
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

describe('OpportunityCard', () => {
  const mockOpportunity: OpportunityListItem = {
    id: 'test-id-123',
    title: 'Test Opportunity Title',
    summary: 'This is a test summary for the opportunity card component.',
    problem_severity: 8.5,
    market_size: 'large',
    monetization_potential: 7.0,
    technical_complexity: 5.0,
    competition_level: 'medium',
    trend_direction: 'growing',
    confidence_level: 0.85,
    analyzed_at: '2025-10-09T12:00:00Z',
  };

  it('renders title and summary', () => {
    render(<OpportunityCard opportunity={mockOpportunity} />);

    expect(screen.getByText('Test Opportunity Title')).toBeInTheDocument();
    expect(screen.getByText(/This is a test summary/)).toBeInTheDocument();
  });

  it('displays all 6 dimensional scores', () => {
    render(<OpportunityCard opportunity={mockOpportunity} />);

    // Check for severity score
    expect(screen.getByText(/8\.5/)).toBeInTheDocument();

    // Check for market size
    expect(screen.getByText(/large/i)).toBeInTheDocument();

    // Check for monetization
    expect(screen.getByText(/7\.0/)).toBeInTheDocument();

    // Check for complexity
    expect(screen.getByText(/5\.0/)).toBeInTheDocument();

    // Check for competition level
    expect(screen.getByText(/medium/i)).toBeInTheDocument();

    // Check for trend direction
    expect(screen.getByText(/growing/i)).toBeInTheDocument();
  });

  it('renders as a link to detail page', () => {
    render(<OpportunityCard opportunity={mockOpportunity} />);

    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/opportunities/test-id-123');
  });

  it('applies hover effect classes', () => {
    const { container } = render(<OpportunityCard opportunity={mockOpportunity} />);

    const card = container.querySelector('.hover\\:shadow-md');
    expect(card).toBeInTheDocument();
  });

  it('applies dark mode classes', () => {
    const { container } = render(<OpportunityCard opportunity={mockOpportunity} />);

    // Check for dark mode background class
    const card = container.querySelector('.dark\\:bg-gray-900');
    expect(card).toBeInTheDocument();
  });

  it('truncates long summaries', () => {
    const longSummary = 'A'.repeat(400); // 400 characters
    const longOpportunity: OpportunityListItem = {
      ...mockOpportunity,
      summary: longSummary,
    };

    const { container } = render(<OpportunityCard opportunity={longOpportunity} />);

    // Check for line-clamp class
    const summary = container.querySelector('.line-clamp-3');
    expect(summary).toBeInTheDocument();
  });
});

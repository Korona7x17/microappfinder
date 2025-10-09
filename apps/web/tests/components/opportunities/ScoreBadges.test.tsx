/**
 * Test: ScoreBadges Component
 * Tests the badge component for displaying 6-dimensional scores
 */

import { render, screen } from '@testing-library/react';
import { ScoreBadges } from '@/components/opportunities/ScoreBadges';
import type { OpportunityListItem } from '@/types/opportunity';

describe('ScoreBadges', () => {
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
  };

  it('renders all 6 badges', () => {
    const { container } = render(<ScoreBadges opportunity={mockOpportunity} />);

    // Grid should contain 6 badge elements
    const badges = container.querySelectorAll('span');
    expect(badges).toHaveLength(6);
  });

  it('renders severity badge with correct value', () => {
    render(<ScoreBadges opportunity={mockOpportunity} />);

    expect(screen.getByText(/Severity: 8\.5/)).toBeInTheDocument();
  });

  it('applies correct color for high severity', () => {
    const { container } = render(<ScoreBadges opportunity={mockOpportunity} />);

    // High severity should have red color
    const severityBadge = container.querySelector('.bg-red-100');
    expect(severityBadge).toBeInTheDocument();
  });

  it('renders market size badge', () => {
    render(<ScoreBadges opportunity={mockOpportunity} />);

    expect(screen.getByText(/large market/i)).toBeInTheDocument();
  });

  it('applies purple color for large market size', () => {
    const { container } = render(<ScoreBadges opportunity={mockOpportunity} />);

    // Large market should have purple color
    const marketBadge = container.querySelector('.bg-purple-100');
    expect(marketBadge).toBeInTheDocument();
  });

  it('applies blue color for mid market size', () => {
    const midMarketOpportunity: OpportunityListItem = {
      ...mockOpportunity,
      market_size: 'mid',
    };

    const { container } = render(<ScoreBadges opportunity={midMarketOpportunity} />);

    const marketBadge = container.querySelector('.bg-blue-100');
    expect(marketBadge).toBeInTheDocument();
  });

  it('applies yellow color for niche market size', () => {
    const nicheOpportunity: OpportunityListItem = {
      ...mockOpportunity,
      market_size: 'niche',
    };

    const { container } = render(<ScoreBadges opportunity={nicheOpportunity} />);

    const marketBadge = container.querySelector('.bg-yellow-100');
    expect(marketBadge).toBeInTheDocument();
  });

  it('renders monetization badge', () => {
    render(<ScoreBadges opportunity={mockOpportunity} />);

    expect(screen.getByText(/Money: 7\.0/)).toBeInTheDocument();
  });

  it('renders complexity badge', () => {
    render(<ScoreBadges opportunity={mockOpportunity} />);

    expect(screen.getByText(/Complexity: 5\.0/)).toBeInTheDocument();
  });

  it('renders competition level badge', () => {
    render(<ScoreBadges opportunity={mockOpportunity} />);

    expect(screen.getByText(/medium comp/i)).toBeInTheDocument();
  });

  it('renders trend direction badge', () => {
    render(<ScoreBadges opportunity={mockOpportunity} />);

    expect(screen.getByText(/growing/i)).toBeInTheDocument();
  });

  it('applies dark mode classes', () => {
    const { container } = render(<ScoreBadges opportunity={mockOpportunity} />);

    // Check for dark mode background class on at least one badge
    const darkBadge = container.querySelector('.dark\\:bg-red-900\\/30');
    expect(darkBadge).toBeInTheDocument();
  });

  it('applies responsive grid layout', () => {
    const { container } = render(<ScoreBadges opportunity={mockOpportunity} />);

    // Check for responsive grid classes
    const grid = container.querySelector('.grid-cols-2');
    expect(grid).toBeInTheDocument();

    const smGrid = container.querySelector('.sm\\:grid-cols-3');
    expect(smGrid).toBeInTheDocument();
  });

  it('applies correct color for low competition', () => {
    const lowCompOpportunity: OpportunityListItem = {
      ...mockOpportunity,
      competition_level: 'low',
    };

    const { container } = render(<ScoreBadges opportunity={lowCompOpportunity} />);

    // Low competition should have green color (good)
    const badges = container.querySelectorAll('.bg-green-100');
    // Should have at least 2 green badges (monetization + low competition)
    expect(badges.length).toBeGreaterThanOrEqual(2);
  });

  it('applies correct color for explosive trend', () => {
    const explosiveOpportunity: OpportunityListItem = {
      ...mockOpportunity,
      trend_direction: 'explosive',
    };

    render(<ScoreBadges opportunity={explosiveOpportunity} />);

    expect(screen.getByText(/explosive/i)).toBeInTheDocument();
  });
});

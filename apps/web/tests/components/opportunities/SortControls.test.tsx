/**
 * Test: SortControls Component
 * Tests the sort dropdown and order toggle
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { SortControls } from '@/components/opportunities/SortControls';

describe('SortControls', () => {
  it('renders sort dropdown', () => {
    render(<SortControls onSortChange={jest.fn()} />);

    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
  });

  it('shows all 4 sort options', () => {
    render(<SortControls onSortChange={jest.fn()} />);

    expect(screen.getByText('Latest')).toBeInTheDocument();
    expect(screen.getByText('Severity')).toBeInTheDocument();
    expect(screen.getByText('Monetization')).toBeInTheDocument();
    expect(screen.getByText('Complexity')).toBeInTheDocument();
  });

  it('defaults to "Latest" (analyzed_at)', () => {
    render(<SortControls onSortChange={jest.fn()} />);

    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('analyzed_at');
  });

  it('defaults to descending order', () => {
    render(<SortControls onSortChange={jest.fn()} />);

    // Descending order shows ↓ arrow
    expect(screen.getByText('↓')).toBeInTheDocument();
  });

  it('calls callback when sort field changes', () => {
    const onSortChange = jest.fn();
    render(<SortControls onSortChange={onSortChange} />);

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'monetization' } });

    expect(onSortChange).toHaveBeenCalledWith('monetization', 'desc');
  });

  it('calls callback when sort order toggles', () => {
    const onSortChange = jest.fn();
    render(<SortControls onSortChange={onSortChange} />);

    const toggleButton = screen.getByText('↓');
    fireEvent.click(toggleButton);

    expect(onSortChange).toHaveBeenCalledWith('analyzed_at', 'asc');
  });

  it('toggles between ASC and DESC', () => {
    render(<SortControls onSortChange={jest.fn()} />);

    const toggleButton = screen.getByText('↓');

    // Click to toggle to ASC
    fireEvent.click(toggleButton);
    expect(screen.getByText('↑')).toBeInTheDocument();

    // Click again to toggle back to DESC
    const ascButton = screen.getByText('↑');
    fireEvent.click(ascButton);
    expect(screen.getByText('↓')).toBeInTheDocument();
  });

  it('applies dark mode classes to dropdown', () => {
    const { container } = render(<SortControls onSortChange={jest.fn()} />);

    const select = container.querySelector('.dark\\:bg-gray-900');
    expect(select).toBeInTheDocument();
  });

  it('applies dark mode classes to toggle button', () => {
    const { container } = render(<SortControls onSortChange={jest.fn()} />);

    const button = container.querySelector('.dark\\:bg-gray-800');
    expect(button).toBeInTheDocument();
  });

  it('calls callback with correct sort field and order combination', () => {
    const onSortChange = jest.fn();
    render(<SortControls onSortChange={onSortChange} />);

    // Change to severity
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'severity' } });

    // Toggle to ASC
    const toggleButton = screen.getByText('↓');
    fireEvent.click(toggleButton);

    // Should have called with severity, desc first, then severity, asc
    expect(onSortChange).toHaveBeenCalledWith('severity', 'desc');
    expect(onSortChange).toHaveBeenCalledWith('severity', 'asc');
  });
});

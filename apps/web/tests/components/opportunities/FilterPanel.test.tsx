/**
 * Test: FilterPanel Component
 * Tests the filter panel with 6 dimensional filters
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FilterPanel } from '@/components/opportunities/FilterPanel';

describe('FilterPanel', () => {
  it('renders filter panel', () => {
    render(<FilterPanel onFilterChange={jest.fn()} />);

    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  it('renders severity range inputs', () => {
    render(<FilterPanel onFilterChange={jest.fn()} />);

    expect(screen.getByLabelText(/severity min/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/severity max/i)).toBeInTheDocument();
  });

  it('renders market size checkboxes', () => {
    render(<FilterPanel onFilterChange={jest.fn()} />);

    expect(screen.getByLabelText(/niche/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/mid/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/large/i)).toBeInTheDocument();
  });

  it('renders competition level checkboxes', () => {
    render(<FilterPanel onFilterChange={jest.fn()} />);

    expect(screen.getByLabelText(/^low$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^medium$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^high$/i)).toBeInTheDocument();
  });

  it('renders clear filters button', () => {
    render(<FilterPanel onFilterChange={jest.fn()} />);

    expect(screen.getByText('Clear Filters')).toBeInTheDocument();
  });

  it('calls onFilterChange when severity changes (debounced)', async () => {
    const onFilterChange = jest.fn();
    render(<FilterPanel onFilterChange={onFilterChange} />);

    const severityMinInput = screen.getByLabelText(/severity min/i);
    fireEvent.change(severityMinInput, { target: { value: '7' } });

    // Should not call immediately
    expect(onFilterChange).not.toHaveBeenCalled();

    // Should call after debounce delay (300ms)
    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalled();
    }, { timeout: 500 });

    expect(onFilterChange).toHaveBeenCalledWith(expect.objectContaining({
      severity_min: 7,
    }));
  });

  it('calls onFilterChange when market size checkbox is toggled', async () => {
    const onFilterChange = jest.fn();
    render(<FilterPanel onFilterChange={onFilterChange} />);

    const largeCheckbox = screen.getByLabelText(/large/i);
    fireEvent.click(largeCheckbox);

    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalled();
    }, { timeout: 500 });

    expect(onFilterChange).toHaveBeenCalledWith(expect.objectContaining({
      market_size: ['large'],
    }));
  });

  it('allows multiple market sizes to be selected', async () => {
    const onFilterChange = jest.fn();
    render(<FilterPanel onFilterChange={onFilterChange} />);

    const largeCheckbox = screen.getByLabelText(/large/i);
    const midCheckbox = screen.getByLabelText(/mid/i);

    fireEvent.click(largeCheckbox);
    fireEvent.click(midCheckbox);

    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalledWith(expect.objectContaining({
        market_size: expect.arrayContaining(['large', 'mid']),
      }));
    }, { timeout: 500 });
  });

  it('clears all filters when Clear Filters button is clicked', async () => {
    const onFilterChange = jest.fn();
    render(<FilterPanel onFilterChange={onFilterChange} />);

    // Set some filters first
    const severityMinInput = screen.getByLabelText(/severity min/i);
    fireEvent.change(severityMinInput, { target: { value: '7' } });

    const largeCheckbox = screen.getByLabelText(/large/i);
    fireEvent.click(largeCheckbox);

    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalled();
    });

    // Clear filters
    onFilterChange.mockClear();
    const clearButton = screen.getByText('Clear Filters');
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalledWith({});
    });
  });

  it('applies dark mode classes', () => {
    const { container } = render(<FilterPanel onFilterChange={jest.fn()} />);

    const darkBg = container.querySelector('.dark\\:bg-gray-900');
    expect(darkBg).toBeInTheDocument();
  });

  it('handles unchecking market size', async () => {
    const onFilterChange = jest.fn();
    render(<FilterPanel onFilterChange={onFilterChange} />);

    const largeCheckbox = screen.getByLabelText(/large/i) as HTMLInputElement;

    // Check it
    fireEvent.click(largeCheckbox);
    await waitFor(() => {
      expect(largeCheckbox.checked).toBe(true);
    });

    // Uncheck it
    fireEvent.click(largeCheckbox);
    await waitFor(() => {
      expect(largeCheckbox.checked).toBe(false);
    });

    // Should eventually call with empty or undefined market_size
    await waitFor(() => {
      const lastCall = onFilterChange.mock.calls[onFilterChange.mock.calls.length - 1][0];
      expect(!lastCall.market_size || lastCall.market_size.length === 0).toBe(true);
    });
  });
});

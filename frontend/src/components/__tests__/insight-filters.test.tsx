import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { InsightFilters } from '../insights/insight-filters';
import { FilterState } from '@/types';

const mockFilters: FilterState = {
  search: '',
  categories: [],
  minConfidence: 0,
  dateRange: null,
};

describe('InsightFilters', () => {
  describe('Search Filter', () => {
    it('renders search input', () => {
      const onFiltersChange = vi.fn();
      render(
        <InsightFilters
          filters={mockFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      expect(screen.getByPlaceholderText('Search insights...')).toBeInTheDocument();
    });

    it('calls onFiltersChange when search text changes', () => {
      const onFiltersChange = vi.fn();
      
      render(
        <InsightFilters
          filters={mockFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      const searchInput = screen.getByPlaceholderText('Search insights...');
      fireEvent.change(searchInput, { target: { value: 'bitcoin' } });
      
      expect(onFiltersChange).toHaveBeenCalledWith({
        ...mockFilters,
        search: 'bitcoin',
      });
    });
  });

  describe('Category Multi-Select', () => {
    it('renders all category checkboxes', () => {
      const onFiltersChange = vi.fn();
      render(
        <InsightFilters
          filters={mockFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      expect(screen.getByLabelText('Mempool')).toBeInTheDocument();
      expect(screen.getByLabelText('Exchange')).toBeInTheDocument();
      expect(screen.getByLabelText('Miner')).toBeInTheDocument();
      expect(screen.getByLabelText('Whale')).toBeInTheDocument();
    });

    it('toggles category selection', () => {
      const onFiltersChange = vi.fn();
      
      render(
        <InsightFilters
          filters={mockFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      const mempoolCheckbox = screen.getByLabelText('Mempool');
      fireEvent.click(mempoolCheckbox);
      
      expect(onFiltersChange).toHaveBeenCalledWith({
        ...mockFilters,
        categories: ['mempool'],
      });
    });

    it('allows multiple category selections', () => {
      const onFiltersChange = vi.fn();
      
      const { rerender } = render(
        <InsightFilters
          filters={mockFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      // Select first category
      fireEvent.click(screen.getByLabelText('Mempool'));
      
      // Update filters with first selection
      const updatedFilters = { ...mockFilters, categories: ['mempool'] };
      rerender(
        <InsightFilters
          filters={updatedFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      // Select second category
      fireEvent.click(screen.getByLabelText('Exchange'));
      
      expect(onFiltersChange).toHaveBeenLastCalledWith({
        ...updatedFilters,
        categories: ['mempool', 'exchange'],
      });
    });

    it('deselects category when clicked again', () => {
      const onFiltersChange = vi.fn();
      
      const filtersWithCategory = {
        ...mockFilters,
        categories: ['mempool'],
      };
      
      render(
        <InsightFilters
          filters={filtersWithCategory}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      fireEvent.click(screen.getByLabelText('Mempool'));
      
      expect(onFiltersChange).toHaveBeenCalledWith({
        ...filtersWithCategory,
        categories: [],
      });
    });
  });

  describe('Confidence Score Slider', () => {
    it('renders confidence slider with initial value', () => {
      const onFiltersChange = vi.fn();
      render(
        <InsightFilters
          filters={mockFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      expect(screen.getByText('Minimum Confidence')).toBeInTheDocument();
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('displays confidence percentage', () => {
      const onFiltersChange = vi.fn();
      const filtersWithConfidence = { ...mockFilters, minConfidence: 0.7 };
      
      render(
        <InsightFilters
          filters={filtersWithConfidence}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      expect(screen.getByText('70%')).toBeInTheDocument();
    });
  });

  describe('Date Range Picker', () => {
    it('renders date range picker button', () => {
      const onFiltersChange = vi.fn();
      render(
        <InsightFilters
          filters={mockFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      expect(screen.getByText('Pick a date range')).toBeInTheDocument();
    });

    it('displays selected date range', () => {
      const onFiltersChange = vi.fn();
      const filtersWithDateRange = {
        ...mockFilters,
        dateRange: {
          start: new Date('2024-01-01'),
          end: new Date('2024-01-31'),
        },
      };
      
      render(
        <InsightFilters
          filters={filtersWithDateRange}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      expect(screen.getByText(/Jan 1, 2024/)).toBeInTheDocument();
      expect(screen.getByText(/Jan 31, 2024/)).toBeInTheDocument();
    });
  });

  describe('Result Count', () => {
    it('displays result count', () => {
      const onFiltersChange = vi.fn();
      render(
        <InsightFilters
          filters={mockFilters}
          onFiltersChange={onFiltersChange}
          resultCount={42}
        />
      );
      
      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText('results')).toBeInTheDocument();
    });

    it('displays singular "result" for count of 1', () => {
      const onFiltersChange = vi.fn();
      render(
        <InsightFilters
          filters={mockFilters}
          onFiltersChange={onFiltersChange}
          resultCount={1}
        />
      );
      
      expect(screen.getByText('result')).toBeInTheDocument();
    });
  });

  describe('Clear Filters', () => {
    it('does not show clear button when no filters are active', () => {
      const onFiltersChange = vi.fn();
      render(
        <InsightFilters
          filters={mockFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      expect(screen.queryByText('Clear Filters')).not.toBeInTheDocument();
    });

    it('shows clear button when filters are active', () => {
      const onFiltersChange = vi.fn();
      const activeFilters = {
        ...mockFilters,
        search: 'bitcoin',
        categories: ['mempool'],
      };
      
      render(
        <InsightFilters
          filters={activeFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      expect(screen.getByText('Clear Filters')).toBeInTheDocument();
    });

    it('clears all filters when clear button is clicked', () => {
      const onFiltersChange = vi.fn();
      const activeFilters = {
        search: 'bitcoin',
        categories: ['mempool', 'exchange'],
        minConfidence: 0.7,
        dateRange: {
          start: new Date('2024-01-01'),
          end: new Date('2024-01-31'),
        },
      };
      
      render(
        <InsightFilters
          filters={activeFilters}
          onFiltersChange={onFiltersChange}
          resultCount={10}
        />
      );
      
      fireEvent.click(screen.getByText('Clear Filters'));
      
      expect(onFiltersChange).toHaveBeenCalledWith({
        search: '',
        categories: [],
        minConfidence: 0,
        dateRange: null,
      });
    });
  });
});

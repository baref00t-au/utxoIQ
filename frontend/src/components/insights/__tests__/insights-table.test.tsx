import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { InsightsTable } from '../insights-table';
import { Insight, SignalType } from '@/types';

// Mock the bookmark button component
vi.mock('../bookmark-button', () => ({
  BookmarkButton: ({ insightId }: { insightId: string }) => (
    <button data-testid={`bookmark-${insightId}`}>Bookmark</button>
  ),
}));

const mockInsights: Insight[] = [
  {
    id: 'insight-1',
    headline: 'High mempool fees detected',
    summary: 'Mempool fees have increased significantly',
    signal_type: 'mempool' as SignalType,
    confidence: 0.92,
    timestamp: '2024-01-01T10:00:00Z',
    block_height: 820000,
    evidence: {
      blocks: [820000],
      transactions: [],
    },
  },
  {
    id: 'insight-2',
    headline: 'Large exchange outflow',
    summary: 'Significant BTC moved from exchanges',
    signal_type: 'exchange' as SignalType,
    confidence: 0.78,
    timestamp: '2024-01-02T12:00:00Z',
    block_height: 820100,
    evidence: {
      blocks: [820100],
      transactions: [],
    },
  },
  {
    id: 'insight-3',
    headline: 'Miner activity spike',
    summary: 'Increased mining activity observed',
    signal_type: 'miner' as SignalType,
    confidence: 0.65,
    timestamp: '2024-01-03T14:00:00Z',
    block_height: 820200,
    evidence: {
      blocks: [820200],
      transactions: [],
    },
  },
];

describe('InsightsTable', () => {
  it('renders insights in table format', () => {
    render(<InsightsTable insights={mockInsights} />);
    
    expect(screen.getByText('High mempool fees detected')).toBeInTheDocument();
    expect(screen.getByText('Large exchange outflow')).toBeInTheDocument();
    expect(screen.getByText('Miner activity spike')).toBeInTheDocument();
  });

  it('displays category badges with correct colors', () => {
    render(<InsightsTable insights={mockInsights} />);
    
    const mempoolBadge = screen.getByText('mempool');
    const exchangeBadge = screen.getByText('exchange');
    const minerBadge = screen.getByText('miner');
    
    expect(mempoolBadge).toBeInTheDocument();
    expect(exchangeBadge).toBeInTheDocument();
    expect(minerBadge).toBeInTheDocument();
  });

  it('displays confidence scores as percentages', () => {
    render(<InsightsTable insights={mockInsights} />);
    
    expect(screen.getByText('92%')).toBeInTheDocument(); // 0.92 * 100
    expect(screen.getByText('78%')).toBeInTheDocument(); // 0.78 * 100
    expect(screen.getByText('65%')).toBeInTheDocument(); // 0.65 * 100
  });

  it('displays block heights with formatting', () => {
    render(<InsightsTable insights={mockInsights} />);
    
    expect(screen.getByText('820,000')).toBeInTheDocument();
    expect(screen.getByText('820,100')).toBeInTheDocument();
    expect(screen.getByText('820,200')).toBeInTheDocument();
  });

  it('renders bookmark buttons for each insight', () => {
    render(<InsightsTable insights={mockInsights} />);
    
    expect(screen.getByTestId('bookmark-insight-1')).toBeInTheDocument();
    expect(screen.getByTestId('bookmark-insight-2')).toBeInTheDocument();
    expect(screen.getByTestId('bookmark-insight-3')).toBeInTheDocument();
  });

  it('sorts by timestamp when header is clicked', async () => {
    render(<InsightsTable insights={mockInsights} />);
    
    const timeHeader = screen.getByRole('button', { name: /sort by time/i });
    fireEvent.click(timeHeader);
    
    await waitFor(() => {
      const rows = screen.getAllByRole('row');
      // First data row should be the earliest timestamp
      expect(rows[1]).toHaveTextContent('Jan 1, 2024');
    });
  });

  it('sorts by confidence when header is clicked', async () => {
    render(<InsightsTable insights={mockInsights} />);
    
    const confidenceHeader = screen.getByRole('button', { name: /sort by confidence/i });
    fireEvent.click(confidenceHeader);
    
    await waitFor(() => {
      const rows = screen.getAllByRole('row');
      // First data row should have lowest confidence (65%)
      expect(rows[1]).toHaveTextContent('65%');
    });
    
    // Click again for descending
    fireEvent.click(confidenceHeader);
    
    await waitFor(() => {
      const rows = screen.getAllByRole('row');
      // First data row should have highest confidence (92%)
      expect(rows[1]).toHaveTextContent('92%');
    });
  });

  it('sorts by category when header is clicked', async () => {
    render(<InsightsTable insights={mockInsights} />);
    
    const categoryHeader = screen.getByRole('button', { name: /sort by category/i });
    fireEvent.click(categoryHeader);
    
    await waitFor(() => {
      const rows = screen.getAllByRole('row');
      // Categories should be sorted alphabetically
      expect(rows[1]).toHaveTextContent('exchange');
    });
  });

  it('supports multi-column sorting', async () => {
    const duplicateTypeInsights = [
      ...mockInsights,
      {
        id: 'insight-4',
        headline: 'Another mempool event',
        summary: 'More mempool activity',
        signal_type: 'mempool' as SignalType,
        confidence: 0.85,
        timestamp: '2024-01-04T16:00:00Z',
        block_height: 820300,
        evidence: { blocks: [820300], transactions: [] },
      },
    ];
    
    render(<InsightsTable insights={duplicateTypeInsights} />);
    
    const categoryHeader = screen.getByRole('button', { name: /sort by category/i });
    const confidenceHeader = screen.getByRole('button', { name: /sort by confidence/i });
    
    // Sort by category first
    fireEvent.click(categoryHeader);
    
    // Then add confidence as secondary sort with shift-click
    fireEvent.click(confidenceHeader, { shiftKey: true });
    
    await waitFor(() => {
      // Should be sorted by category, then confidence within each category
      const rows = screen.getAllByRole('row');
      expect(rows.length).toBeGreaterThan(1);
    });
  });

  it('calls onSortingChange callback when sorting changes', async () => {
    const onSortingChange = vi.fn();
    render(<InsightsTable insights={mockInsights} onSortingChange={onSortingChange} />);
    
    const timeHeader = screen.getByRole('button', { name: /sort by time/i });
    fireEvent.click(timeHeader);
    
    await waitFor(() => {
      expect(onSortingChange).toHaveBeenCalledWith([
        { id: 'timestamp', desc: false }
      ]);
    });
  });

  it('applies initial sorting state', () => {
    render(
      <InsightsTable
        insights={mockInsights}
        initialSorting={[{ id: 'confidence', desc: true }]}
      />
    );
    
    const rows = screen.getAllByRole('row');
    // Should be sorted by confidence descending, so 92% should be first
    expect(rows[1]).toHaveTextContent('92%');
  });

  it('renders empty state when no insights', () => {
    render(<InsightsTable insights={[]} />);
    
    expect(screen.getByText('No results.')).toBeInTheDocument();
  });

  it('formats timestamps correctly', () => {
    render(<InsightsTable insights={mockInsights} />);
    
    // Should show both date and time
    expect(screen.getByText('Jan 1, 2024')).toBeInTheDocument();
    expect(screen.getByText('10:00:00')).toBeInTheDocument();
  });

  it('handles insights without block height', () => {
    const insightWithoutBlock: Insight = {
      ...mockInsights[0],
      id: 'insight-no-block',
      block_height: undefined,
    };
    
    render(<InsightsTable insights={[insightWithoutBlock]} />);
    
    // Should show em dash for missing block height
    expect(screen.getByText('—')).toBeInTheDocument();
  });
});

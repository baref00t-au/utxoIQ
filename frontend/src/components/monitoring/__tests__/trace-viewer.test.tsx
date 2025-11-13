import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TraceViewer } from '../trace-viewer';

// Mock API functions
vi.mock('@/lib/api', () => ({
  fetchTrace: vi.fn(() =>
    Promise.resolve({
      trace_id: 'trace-123',
      total_duration_ms: 1500,
      spans: [
        {
          span_id: 'span-1',
          name: 'HTTP GET /api/insights',
          start_time: '2024-01-01T00:00:00Z',
          end_time: '2024-01-01T00:00:01.5Z',
          duration_ms: 1500,
          status: 'ok',
          attributes: { method: 'GET', path: '/api/insights' },
        },
        {
          span_id: 'span-2',
          parent_span_id: 'span-1',
          name: 'Database Query',
          start_time: '2024-01-01T00:00:00.5Z',
          end_time: '2024-01-01T00:00:01.2Z',
          duration_ms: 700,
          status: 'ok',
          attributes: { query: 'SELECT * FROM insights' },
        },
      ],
    })
  ),
}));

describe('TraceViewer', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('renders trace search form', () => {
    render(<TraceViewer />, { wrapper });

    expect(screen.getByText('Trace Search')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Enter trace ID/i)).toBeInTheDocument();
  });

  it('allows entering trace ID', () => {
    render(<TraceViewer />, { wrapper });

    const traceInput = screen.getByPlaceholderText(/Enter trace ID/i);
    fireEvent.change(traceInput, { target: { value: 'trace-123' } });

    expect(traceInput).toHaveValue('trace-123');
  });

  it('displays trace details after search', async () => {
    render(<TraceViewer />, { wrapper });

    const traceInput = screen.getByPlaceholderText(/Enter trace ID/i);
    fireEvent.change(traceInput, { target: { value: 'trace-123' } });

    const searchButton = screen.getByRole('button', { name: /Search/i });
    fireEvent.click(searchButton);

    // Trace summary should appear
    expect(await screen.findByText('Trace Summary')).toBeInTheDocument();
    expect(await screen.findByText(/Total Duration/i)).toBeInTheDocument();
  });
});

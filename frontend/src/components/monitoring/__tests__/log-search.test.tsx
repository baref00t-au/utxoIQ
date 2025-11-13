import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LogSearch } from '../log-search';

// Mock API functions
vi.mock('@/lib/api', () => ({
  searchLogs: vi.fn(() =>
    Promise.resolve({
      logs: [
        {
          id: 'log-1',
          timestamp: '2024-01-01T00:00:00Z',
          severity: 'ERROR',
          service: 'web-api',
          message: 'Database connection failed',
          metadata: { error_code: 'DB_CONN_ERR' },
        },
        {
          id: 'log-2',
          timestamp: '2024-01-01T00:01:00Z',
          severity: 'INFO',
          service: 'web-api',
          message: 'Request processed successfully',
          metadata: { duration_ms: 120 },
        },
      ],
    })
  ),
  fetchLogContext: vi.fn(() =>
    Promise.resolve({
      logs: [
        {
          id: 'log-0',
          timestamp: '2024-01-01T00:00:00Z',
          severity: 'INFO',
          service: 'web-api',
          message: 'Starting request',
        },
        {
          id: 'log-1',
          timestamp: '2024-01-01T00:00:00Z',
          severity: 'ERROR',
          service: 'web-api',
          message: 'Database connection failed',
        },
      ],
    })
  ),
}));

describe('LogSearch', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('renders search form', () => {
    render(<LogSearch />, { wrapper });

    expect(screen.getByText('Log Search')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Enter search terms/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Search Logs/i })).toBeInTheDocument();
  });

  it('allows entering search query', () => {
    render(<LogSearch />, { wrapper });

    const searchInput = screen.getByPlaceholderText(/Enter search terms/i);
    fireEvent.change(searchInput, { target: { value: 'error' } });

    expect(searchInput).toHaveValue('error');
  });

  it('displays search results after search', async () => {
    render(<LogSearch />, { wrapper });

    const searchButton = screen.getByRole('button', { name: /Search Logs/i });
    fireEvent.click(searchButton);

    // Results should appear
    expect(await screen.findByText('Database connection failed')).toBeInTheDocument();
    expect(await screen.findByText('Request processed successfully')).toBeInTheDocument();
  });
});

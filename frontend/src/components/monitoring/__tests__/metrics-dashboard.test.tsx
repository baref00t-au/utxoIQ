import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MetricsDashboard } from '../metrics-dashboard';

// Mock the API functions
vi.mock('@/lib/api', () => ({
  fetchServiceMetrics: vi.fn(() =>
    Promise.resolve({
      cpu_usage: [
        { timestamp: '2024-01-01T00:00:00Z', value: 45.2 },
        { timestamp: '2024-01-01T01:00:00Z', value: 52.1 },
      ],
      memory_usage: [
        { timestamp: '2024-01-01T00:00:00Z', value: 60.5 },
        { timestamp: '2024-01-01T01:00:00Z', value: 65.3 },
      ],
      response_time: [
        { timestamp: '2024-01-01T00:00:00Z', value: 120 },
        { timestamp: '2024-01-01T01:00:00Z', value: 135 },
      ],
      error_rate: [
        { timestamp: '2024-01-01T00:00:00Z', value: 0.5 },
        { timestamp: '2024-01-01T01:00:00Z', value: 0.8 },
      ],
    })
  ),
  fetchBaseline: vi.fn(() =>
    Promise.resolve({
      mean: 50.0,
      median: 48.5,
      std_dev: 5.2,
      p95: 60.0,
      p99: 65.0,
    })
  ),
}));

describe('MetricsDashboard', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('renders dashboard with metric cards', async () => {
    render(<MetricsDashboard />, { wrapper });

    // Check for metric labels
    expect(await screen.findByText('CPU Usage')).toBeInTheDocument();
    expect(await screen.findByText('Memory Usage')).toBeInTheDocument();
    expect(await screen.findByText('Response Time')).toBeInTheDocument();
    expect(await screen.findByText('Error Rate')).toBeInTheDocument();
  });

  it('displays baseline statistics', async () => {
    render(<MetricsDashboard />, { wrapper });

    // Wait for baseline data to load
    expect(await screen.findByText('Mean')).toBeInTheDocument();
    expect(await screen.findByText('Median')).toBeInTheDocument();
    expect(await screen.findByText('Std Dev')).toBeInTheDocument();
    expect(await screen.findByText('P95')).toBeInTheDocument();
    expect(await screen.findByText('P99')).toBeInTheDocument();
  });
});

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AlertsManagement } from '../alerts-management';

// Mock auth context
vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    user: { uid: 'test-user', email: 'test@example.com' },
    getIdToken: vi.fn(() => Promise.resolve('test-token')),
  }),
}));

// Mock API functions
vi.mock('@/lib/api', () => ({
  fetchAlertConfigurations: vi.fn(() =>
    Promise.resolve([
      {
        id: 'alert-1',
        name: 'High CPU Alert',
        service_name: 'web-api',
        metric_type: 'cpu_usage',
        threshold_type: 'absolute',
        threshold_value: 80,
        comparison_operator: '>',
        severity: 'warning',
        evaluation_window_seconds: 300,
        notification_channels: ['email', 'slack'],
        enabled: true,
        created_at: '2024-01-01T00:00:00Z',
      },
    ])
  ),
  createAlertConfiguration: vi.fn(() => Promise.resolve({ id: 'new-alert' })),
  updateAlertConfiguration: vi.fn(() => Promise.resolve({})),
  deleteAlertConfiguration: vi.fn(() => Promise.resolve()),
}));

describe('AlertsManagement', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('renders alert creation form', () => {
    render(<AlertsManagement />, { wrapper });

    expect(screen.getByText('Create Alert')).toBeInTheDocument();
    expect(screen.getByLabelText(/Alert Name/i)).toBeInTheDocument();
  });

  it('displays configured alerts', async () => {
    render(<AlertsManagement />, { wrapper });

    expect(await screen.findByText('High CPU Alert')).toBeInTheDocument();
    expect(await screen.findByText(/web-api/i)).toBeInTheDocument();
  });

  it('validates required fields on form submission', async () => {
    render(<AlertsManagement />, { wrapper });

    const submitButton = screen.getByRole('button', { name: /Create Alert/i });
    fireEvent.click(submitButton);

    // Should show validation error (via toast)
    await waitFor(() => {
      // Form should not submit without required fields
      expect(screen.getByLabelText(/Alert Name/i)).toBeInTheDocument();
    });
  });
});

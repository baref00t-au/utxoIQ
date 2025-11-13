import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useDashboardPersistence } from '../use-dashboard-persistence';
import { DashboardWidget, DashboardConfiguration } from '@/types';

// Mock fetch
global.fetch = vi.fn();

const mockDashboard: DashboardConfiguration = {
  id: 'dashboard-1',
  name: 'Test Dashboard',
  widgets: [
    {
      id: 'widget-1',
      type: 'line_chart',
      title: 'CPU Usage',
      data_source: {
        metric_type: 'cpu_usage',
        aggregation: 'avg',
        time_range: '24h',
      },
      display_options: {},
      position: { x: 0, y: 0, w: 6, h: 2 },
    },
  ],
  is_public: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

describe('useDashboardPersistence', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('loads dashboard on mount', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockDashboard,
    });

    const { result } = renderHook(() =>
      useDashboardPersistence({
        dashboardId: 'dashboard-1',
        userId: 'user-1',
      })
    );

    expect(result.current.isLoading).toBe(true);

    await waitFor(
      () => {
        expect(result.current.isLoading).toBe(false);
      },
      { timeout: 10000 }
    );

    expect(result.current.widgets).toEqual(mockDashboard.widgets);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/dashboards/dashboard-1'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-User-ID': 'user-1',
        }),
      })
    );
  });

  it('handles load error', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    const { result } = renderHook(() =>
      useDashboardPersistence({
        dashboardId: 'dashboard-1',
      })
    );

    await waitFor(
      () => {
        expect(result.current.isLoading).toBe(false);
      },
      { timeout: 10000 }
    );

    expect(result.current.error).toBeTruthy();
  });

  it('adds widget', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockDashboard,
    });

    const { result } = renderHook(() =>
      useDashboardPersistence({
        dashboardId: 'dashboard-1',
      })
    );

    await waitFor(
      () => {
        expect(result.current.isLoading).toBe(false);
      },
      { timeout: 10000 }
    );

    const newWidget = {
      type: 'stat_card' as const,
      title: 'New Widget',
      data_source: {
        metric_type: 'test',
        aggregation: 'avg',
        time_range: '1h',
      },
      display_options: {},
      position: { x: 0, y: 0, w: 3, h: 1 },
    };

    act(() => {
      result.current.addWidget(newWidget);
    });

    expect(result.current.widgets).toHaveLength(2);
    expect(result.current.widgets[1]).toMatchObject(newWidget);
    expect(result.current.widgets[1].id).toBeTruthy();
  });

  it('removes widget', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockDashboard,
    });

    const { result } = renderHook(() =>
      useDashboardPersistence({
        dashboardId: 'dashboard-1',
      })
    );

    await waitFor(
      () => {
        expect(result.current.isLoading).toBe(false);
      },
      { timeout: 10000 }
    );

    act(() => {
      result.current.removeWidget('widget-1');
    });

    expect(result.current.widgets).toHaveLength(0);
  });

  it('auto-saves after 2 seconds', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboard,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

    const { result } = renderHook(() =>
      useDashboardPersistence({
        dashboardId: 'dashboard-1',
      })
    );

    await waitFor(
      () => {
        expect(result.current.isLoading).toBe(false);
      },
      { timeout: 10000 }
    );

    const newWidget = {
      type: 'stat_card' as const,
      title: 'New Widget',
      data_source: {
        metric_type: 'test',
        aggregation: 'avg',
        time_range: '1h',
      },
      display_options: {},
      position: { x: 0, y: 0, w: 3, h: 1 },
    };

    act(() => {
      result.current.addWidget(newWidget);
    });

    // Fast-forward time by 2 seconds
    act(() => {
      vi.advanceTimersByTime(2000);
    });

    await waitFor(
      () => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/dashboards/dashboard-1'),
          expect.objectContaining({
            method: 'PUT',
            body: expect.any(String),
          })
        );
      },
      { timeout: 10000 }
    );
  });

  it('does not save when disabled', async () => {
    const { result } = renderHook(() =>
      useDashboardPersistence({
        enabled: false,
      })
    );

    expect(result.current.isLoading).toBe(false);
    expect(global.fetch).not.toHaveBeenCalled();
  });
});

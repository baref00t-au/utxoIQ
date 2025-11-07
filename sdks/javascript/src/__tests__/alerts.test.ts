/**
 * Tests for alerts resource
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { AxiosInstance } from 'axios';
import { AlertsResource } from '../resources/alerts';

describe('AlertsResource', () => {
  let mockAxios: AxiosInstance;
  let alerts: AlertsResource;

  beforeEach(() => {
    mockAxios = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    } as any;
    alerts = new AlertsResource(mockAxios);
  });

  it('should list alerts', async () => {
    const mockData = {
      alerts: [
        {
          id: 'alert-1',
          userId: 'user-123',
          signalType: 'mempool',
          threshold: 100.0,
          operator: 'gt',
          isActive: true,
          createdAt: '2025-11-07T10:00:00Z',
        },
      ],
    };
    (mockAxios.get as any).mockResolvedValue({ data: mockData });

    const result = await alerts.list();

    expect(result).toHaveLength(1);
    expect(result[0].signalType).toBe('mempool');
    expect(mockAxios.get).toHaveBeenCalledWith('/alerts', { params: undefined });
  });

  it('should create alert', async () => {
    const mockData = {
      id: 'alert-new',
      userId: 'user-123',
      signalType: 'exchange',
      threshold: 1000.0,
      operator: 'gt',
      isActive: true,
      createdAt: '2025-11-07T10:00:00Z',
      notificationChannel: 'email',
    };
    (mockAxios.post as any).mockResolvedValue({ data: mockData });

    const result = await alerts.create({
      signalType: 'exchange',
      threshold: 1000.0,
      operator: 'gt',
    });

    expect(result.signalType).toBe('exchange');
    expect(result.threshold).toBe(1000.0);
    expect(mockAxios.post).toHaveBeenCalledWith('/alerts', {
      signal_type: 'exchange',
      threshold: 1000.0,
      operator: 'gt',
      notification_channel: 'email',
      is_active: true,
    });
  });

  it('should update alert', async () => {
    const mockData = {
      id: 'alert-1',
      userId: 'user-123',
      signalType: 'mempool',
      threshold: 150.0,
      operator: 'gt',
      isActive: false,
      createdAt: '2025-11-07T10:00:00Z',
    };
    (mockAxios.put as any).mockResolvedValue({ data: mockData });

    const result = await alerts.update('alert-1', {
      threshold: 150.0,
      isActive: false,
    });

    expect(result.threshold).toBe(150.0);
    expect(result.isActive).toBe(false);
    expect(mockAxios.put).toHaveBeenCalledWith('/alerts/alert-1', {
      threshold: 150.0,
      is_active: false,
    });
  });

  it('should delete alert', async () => {
    (mockAxios.delete as any).mockResolvedValue({ data: {} });

    const result = await alerts.delete('alert-1');

    expect(result).toBe(true);
    expect(mockAxios.delete).toHaveBeenCalledWith('/alerts/alert-1');
  });
});

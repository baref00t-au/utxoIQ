/**
 * Tests for insights resource
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { AxiosInstance } from 'axios';
import { InsightsResource } from '../resources/insights';

describe('InsightsResource', () => {
  let mockAxios: AxiosInstance;
  let insights: InsightsResource;

  beforeEach(() => {
    mockAxios = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    } as any;
    insights = new InsightsResource(mockAxios);
  });

  it('should get latest insights', async () => {
    const mockData = {
      insights: [
        {
          id: 'insight-1',
          signalType: 'mempool',
          headline: 'Test Insight',
          summary: 'Test summary',
          confidence: 0.85,
          timestamp: '2025-11-07T10:00:00Z',
          blockHeight: 800000,
          evidence: [],
          tags: ['test'],
          isPredictive: false,
        },
      ],
    };
    (mockAxios.get as any).mockResolvedValue({ data: mockData });

    const result = await insights.getLatest({ limit: 10 });

    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('insight-1');
    expect(mockAxios.get).toHaveBeenCalledWith('/insights/latest', {
      params: { limit: 10 },
    });
  });

  it('should get public insights', async () => {
    const mockData = { insights: [] };
    (mockAxios.get as any).mockResolvedValue({ data: mockData });

    const result = await insights.getPublic({ limit: 20 });

    expect(result).toEqual([]);
    expect(mockAxios.get).toHaveBeenCalledWith('/insights/public', {
      params: { limit: 20 },
    });
  });

  it('should get insight by ID', async () => {
    const mockData = {
      id: 'insight-123',
      signalType: 'exchange',
      headline: 'Exchange Inflow Spike',
      summary: 'Large inflow detected',
      confidence: 0.92,
      timestamp: '2025-11-07T10:00:00Z',
      blockHeight: 800001,
      evidence: [],
      tags: [],
      isPredictive: false,
    };
    (mockAxios.get as any).mockResolvedValue({ data: mockData });

    const result = await insights.getById('insight-123');

    expect(result.id).toBe('insight-123');
    expect(result.signalType).toBe('exchange');
    expect(mockAxios.get).toHaveBeenCalledWith('/insight/insight-123');
  });

  it('should search insights', async () => {
    const mockData = { insights: [] };
    (mockAxios.get as any).mockResolvedValue({ data: mockData });

    await insights.search({ query: 'mempool', limit: 10 });

    expect(mockAxios.get).toHaveBeenCalledWith('/insights/search', {
      params: { q: 'mempool', limit: 10, category: undefined },
    });
  });
});

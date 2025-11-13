import { describe, it, expect } from 'vitest';
import { Insight, FilterState, SignalType } from '@/types';

// Mock insights data for testing
const createMockInsight = (overrides: Partial<Insight> = {}): Insight => ({
  id: Math.random().toString(),
  signal_type: 'mempool',
  headline: 'Test Insight',
  summary: 'Test summary',
  confidence: 0.8,
  timestamp: new Date().toISOString(),
  block_height: 800000,
  evidence: [],
  tags: [],
  ...overrides,
});

// Filter logic extracted for testing (same as in insight-feed.tsx)
const applyFilters = (insights: Insight[], filters: FilterState): Insight[] => {
  const startTime = performance.now();
  
  const filtered = insights.filter((insight) => {
    // Category filter (AND logic with multiple categories)
    if (filters.categories.length > 0 && 
        !filters.categories.includes(insight.signal_type)) {
      return false;
    }

    // Confidence filter
    if (insight.confidence < filters.minConfidence) {
      return false;
    }

    // Search filter (full-text search in headline and summary)
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      const matchesHeadline = insight.headline.toLowerCase().includes(searchLower);
      const matchesSummary = insight.summary.toLowerCase().includes(searchLower);
      if (!matchesHeadline && !matchesSummary) {
        return false;
      }
    }

    // Date range filter
    if (filters.dateRange) {
      const insightDate = new Date(insight.timestamp);
      if (insightDate < filters.dateRange.start || 
          insightDate > filters.dateRange.end) {
        return false;
      }
    }

    return true;
  });

  const endTime = performance.now();
  const filterTime = endTime - startTime;
  
  return filtered;
};

describe('Insight Feed Filter Logic', () => {
  describe('Category Filter', () => {
    it('filters by single category', () => {
      const insights = [
        createMockInsight({ signal_type: 'mempool' }),
        createMockInsight({ signal_type: 'exchange' }),
        createMockInsight({ signal_type: 'miner' }),
      ];

      const filters: FilterState = {
        search: '',
        categories: ['mempool'],
        minConfidence: 0,
        dateRange: null,
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(1);
      expect(result[0].signal_type).toBe('mempool');
    });

    it('filters by multiple categories (OR logic)', () => {
      const insights = [
        createMockInsight({ signal_type: 'mempool' }),
        createMockInsight({ signal_type: 'exchange' }),
        createMockInsight({ signal_type: 'miner' }),
        createMockInsight({ signal_type: 'whale' }),
      ];

      const filters: FilterState = {
        search: '',
        categories: ['mempool', 'exchange'],
        minConfidence: 0,
        dateRange: null,
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(2);
      expect(result.map(i => i.signal_type)).toEqual(['mempool', 'exchange']);
    });

    it('returns all insights when no categories selected', () => {
      const insights = [
        createMockInsight({ signal_type: 'mempool' }),
        createMockInsight({ signal_type: 'exchange' }),
      ];

      const filters: FilterState = {
        search: '',
        categories: [],
        minConfidence: 0,
        dateRange: null,
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(2);
    });
  });

  describe('Confidence Filter', () => {
    it('filters by minimum confidence', () => {
      const insights = [
        createMockInsight({ confidence: 0.5 }),
        createMockInsight({ confidence: 0.7 }),
        createMockInsight({ confidence: 0.9 }),
      ];

      const filters: FilterState = {
        search: '',
        categories: [],
        minConfidence: 0.7,
        dateRange: null,
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(2);
      expect(result.every(i => i.confidence >= 0.7)).toBe(true);
    });

    it('includes insights with exact confidence threshold', () => {
      const insights = [
        createMockInsight({ confidence: 0.7 }),
      ];

      const filters: FilterState = {
        search: '',
        categories: [],
        minConfidence: 0.7,
        dateRange: null,
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(1);
    });
  });

  describe('Search Filter', () => {
    it('searches in headline', () => {
      const insights = [
        createMockInsight({ headline: 'Bitcoin price surge' }),
        createMockInsight({ headline: 'Ethereum update' }),
      ];

      const filters: FilterState = {
        search: 'bitcoin',
        categories: [],
        minConfidence: 0,
        dateRange: null,
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(1);
      expect(result[0].headline).toContain('Bitcoin');
    });

    it('searches in summary', () => {
      const insights = [
        createMockInsight({ 
          headline: 'Market Update',
          summary: 'Bitcoin shows strong momentum' 
        }),
        createMockInsight({ 
          headline: 'Market Update',
          summary: 'Ethereum shows weak momentum' 
        }),
      ];

      const filters: FilterState = {
        search: 'bitcoin',
        categories: [],
        minConfidence: 0,
        dateRange: null,
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(1);
      expect(result[0].summary).toContain('Bitcoin');
    });

    it('is case-insensitive', () => {
      const insights = [
        createMockInsight({ headline: 'BITCOIN SURGE' }),
      ];

      const filters: FilterState = {
        search: 'bitcoin',
        categories: [],
        minConfidence: 0,
        dateRange: null,
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(1);
    });

    it('matches partial words', () => {
      const insights = [
        createMockInsight({ headline: 'Bitcoin price increases' }),
      ];

      const filters: FilterState = {
        search: 'bit',
        categories: [],
        minConfidence: 0,
        dateRange: null,
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(1);
    });
  });

  describe('Date Range Filter', () => {
    it('filters by date range', () => {
      const insights = [
        createMockInsight({ timestamp: '2024-01-15T10:00:00Z' }),
        createMockInsight({ timestamp: '2024-02-15T10:00:00Z' }),
        createMockInsight({ timestamp: '2024-03-15T10:00:00Z' }),
      ];

      const filters: FilterState = {
        search: '',
        categories: [],
        minConfidence: 0,
        dateRange: {
          start: new Date('2024-02-01'),
          end: new Date('2024-02-28'),
        },
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(1);
      expect(result[0].timestamp).toBe('2024-02-15T10:00:00Z');
    });

    it('includes insights on boundary dates', () => {
      const insights = [
        createMockInsight({ timestamp: '2024-01-01T00:00:00Z' }),
        createMockInsight({ timestamp: '2024-01-31T23:59:59Z' }),
      ];

      const filters: FilterState = {
        search: '',
        categories: [],
        minConfidence: 0,
        dateRange: {
          start: new Date('2024-01-01'),
          end: new Date('2024-01-31T23:59:59Z'),
        },
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(2);
    });
  });

  describe('Combined Filters (AND Logic)', () => {
    it('applies all filters together', () => {
      const insights = [
        createMockInsight({
          signal_type: 'mempool',
          headline: 'Bitcoin mempool congestion',
          confidence: 0.8,
          timestamp: '2024-01-15T10:00:00Z',
        }),
        createMockInsight({
          signal_type: 'exchange',
          headline: 'Bitcoin exchange flow',
          confidence: 0.6,
          timestamp: '2024-01-15T10:00:00Z',
        }),
        createMockInsight({
          signal_type: 'mempool',
          headline: 'Ethereum mempool update',
          confidence: 0.9,
          timestamp: '2024-01-15T10:00:00Z',
        }),
      ];

      const filters: FilterState = {
        search: 'bitcoin',
        categories: ['mempool'],
        minConfidence: 0.7,
        dateRange: {
          start: new Date('2024-01-01'),
          end: new Date('2024-01-31'),
        },
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(1);
      expect(result[0].headline).toBe('Bitcoin mempool congestion');
    });

    it('returns empty array when no insights match all criteria', () => {
      const insights = [
        createMockInsight({
          signal_type: 'exchange',
          headline: 'Bitcoin update',
          confidence: 0.5,
        }),
      ];

      const filters: FilterState = {
        search: 'bitcoin',
        categories: ['mempool'],
        minConfidence: 0.7,
        dateRange: null,
      };

      const result = applyFilters(insights, filters);
      expect(result).toHaveLength(0);
    });
  });

  describe('Performance', () => {
    it('filters large dataset within 500ms', () => {
      // Create 10,000 insights
      const insights = Array.from({ length: 10000 }, (_, i) =>
        createMockInsight({
          signal_type: ['mempool', 'exchange', 'miner', 'whale'][i % 4] as SignalType,
          headline: `Insight ${i}`,
          confidence: Math.random(),
          timestamp: new Date(Date.now() - i * 1000).toISOString(),
        })
      );

      const filters: FilterState = {
        search: 'Insight',
        categories: ['mempool', 'exchange'],
        minConfidence: 0.5,
        dateRange: null,
      };

      const startTime = performance.now();
      const result = applyFilters(insights, filters);
      const endTime = performance.now();
      const filterTime = endTime - startTime;

      // Should complete within 500ms as per requirements
      expect(filterTime).toBeLessThan(500);
      expect(result.length).toBeGreaterThan(0);
    });

    it('handles empty insights array efficiently', () => {
      const insights: Insight[] = [];
      const filters: FilterState = {
        search: 'test',
        categories: ['mempool'],
        minConfidence: 0.7,
        dateRange: null,
      };

      const startTime = performance.now();
      const result = applyFilters(insights, filters);
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(10);
      expect(result).toHaveLength(0);
    });
  });
});

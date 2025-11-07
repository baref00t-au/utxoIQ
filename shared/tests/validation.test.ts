/**
 * Unit tests for Zod validation schemas
 */

import { describe, it, expect } from 'vitest';
import {
  InsightSchema,
  SignalSchema,
  AlertSchema,
  UserFeedbackSchema,
  PredictiveSignalSchema,
  EmailPreferencesSchema,
  WhiteLabelConfigSchema,
} from '../schemas/validation';

describe('InsightSchema', () => {
  it('should validate a valid insight', () => {
    const validInsight = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      signal_type: 'mempool',
      headline: 'Mempool fees spike to 100 sat/vB',
      summary: 'Network congestion detected with significant fee increases',
      confidence: 0.85,
      timestamp: new Date(),
      block_height: 800000,
      evidence: [
        {
          type: 'block',
          id: '800000',
          description: 'Block at height 800000',
          url: 'https://example.com/block/800000',
        },
      ],
      tags: ['mempool', 'fees'],
    };

    const result = InsightSchema.safeParse(validInsight);
    expect(result.success).toBe(true);
  });

  it('should reject insight with invalid confidence', () => {
    const invalidInsight = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      signal_type: 'mempool',
      headline: 'Test',
      summary: 'Test summary',
      confidence: 1.5, // Invalid: > 1
      timestamp: new Date(),
      block_height: 800000,
      evidence: [],
      tags: [],
    };

    const result = InsightSchema.safeParse(invalidInsight);
    expect(result.success).toBe(false);
  });
});

describe('SignalSchema', () => {
  it('should validate a valid signal', () => {
    const validSignal = {
      type: 'exchange',
      strength: 0.75,
      data: { inflow: 1000, exchange: 'Binance' },
      block_height: 800000,
      transaction_ids: ['tx1', 'tx2'],
      entity_ids: ['entity1'],
    };

    const result = SignalSchema.safeParse(validSignal);
    expect(result.success).toBe(true);
  });

  it('should validate predictive signal with confidence interval', () => {
    const predictiveSignal = {
      type: 'predictive',
      strength: 0.8,
      data: { forecast: 50 },
      block_height: 800000,
      transaction_ids: [],
      entity_ids: [],
      is_predictive: true,
      prediction_confidence_interval: [45, 55],
    };

    const result = SignalSchema.safeParse(predictiveSignal);
    expect(result.success).toBe(true);
  });
});

describe('AlertSchema', () => {
  it('should validate a valid alert', () => {
    const validAlert = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      user_id: 'user123',
      signal_type: 'mempool',
      threshold: 100,
      operator: 'gt',
      is_active: true,
      created_at: new Date(),
    };

    const result = AlertSchema.safeParse(validAlert);
    expect(result.success).toBe(true);
  });
});

describe('UserFeedbackSchema', () => {
  it('should validate user feedback', () => {
    const validFeedback = {
      insight_id: '123e4567-e89b-12d3-a456-426614174000',
      user_id: 'user123',
      rating: 'useful',
      timestamp: new Date(),
      comment: 'Very helpful insight',
    };

    const result = UserFeedbackSchema.safeParse(validFeedback);
    expect(result.success).toBe(true);
  });

  it('should reject invalid rating', () => {
    const invalidFeedback = {
      insight_id: '123e4567-e89b-12d3-a456-426614174000',
      user_id: 'user123',
      rating: 'invalid_rating',
      timestamp: new Date(),
    };

    const result = UserFeedbackSchema.safeParse(invalidFeedback);
    expect(result.success).toBe(false);
  });
});

describe('EmailPreferencesSchema', () => {
  it('should validate email preferences with quiet hours', () => {
    const validPrefs = {
      user_id: 'user123',
      daily_brief_enabled: true,
      frequency: 'daily',
      signal_filters: ['mempool', 'exchange'],
      quiet_hours: {
        start: '22:00',
        end: '08:00',
      },
    };

    const result = EmailPreferencesSchema.safeParse(validPrefs);
    expect(result.success).toBe(true);
  });

  it('should reject invalid time format', () => {
    const invalidPrefs = {
      user_id: 'user123',
      daily_brief_enabled: true,
      frequency: 'daily',
      signal_filters: [],
      quiet_hours: {
        start: '25:00', // Invalid hour
        end: '08:00',
      },
    };

    const result = EmailPreferencesSchema.safeParse(invalidPrefs);
    expect(result.success).toBe(false);
  });
});

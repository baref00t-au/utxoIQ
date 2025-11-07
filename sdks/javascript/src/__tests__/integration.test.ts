/**
 * Integration tests for JavaScript SDK
 * 
 * These tests verify end-to-end functionality with the API.
 * They are skipped by default and require a valid API key.
 * Run with: UTXOIQ_API_KEY=your-key npm test -- integration
 */

import { describe, it, expect, beforeAll } from 'vitest';
import { UtxoIQClient } from '../client';
import { AuthenticationError, NotFoundError } from '../errors';

const API_KEY = process.env.UTXOIQ_API_KEY;
const RUN_INTEGRATION = process.env.RUN_INTEGRATION === 'true' || API_KEY;

describe.skipIf(!RUN_INTEGRATION)('Integration Tests', () => {
  let client: UtxoIQClient;
  let guestClient: UtxoIQClient;

  beforeAll(() => {
    if (!API_KEY) {
      throw new Error('UTXOIQ_API_KEY environment variable not set');
    }
    client = new UtxoIQClient({ apiKey: API_KEY });
    guestClient = new UtxoIQClient(); // No auth for Guest Mode
  });

  describe('Insights', () => {
    it('should get latest insights', async () => {
      const insights = await client.insights.getLatest({ limit: 5 });
      expect(Array.isArray(insights)).toBe(true);
      expect(insights.length).toBeLessThanOrEqual(5);
      if (insights.length > 0) {
        expect(insights[0]).toHaveProperty('id');
        expect(insights[0]).toHaveProperty('headline');
        expect(insights[0]).toHaveProperty('confidence');
      }
    });

    it('should get public insights in Guest Mode', async () => {
      const insights = await guestClient.insights.getPublic({ limit: 10 });
      expect(Array.isArray(insights)).toBe(true);
      expect(insights.length).toBeLessThanOrEqual(20); // Guest Mode limit
    });

    it('should get insight by ID', async () => {
      const insights = await client.insights.getLatest({ limit: 1 });
      if (insights.length > 0) {
        const insightId = insights[0].id;
        const insight = await client.insights.getById(insightId);
        expect(insight.id).toBe(insightId);
      }
    });

    it('should filter by category', async () => {
      const insights = await client.insights.getLatest({
        limit: 10,
        category: 'mempool',
      });
      expect(Array.isArray(insights)).toBe(true);
      if (insights.length > 0) {
        insights.forEach((insight) => {
          expect(insight.signalType).toBe('mempool');
        });
      }
    });

    it('should filter by minimum confidence', async () => {
      const insights = await client.insights.getLatest({
        limit: 10,
        minConfidence: 0.8,
      });
      expect(Array.isArray(insights)).toBe(true);
      if (insights.length > 0) {
        insights.forEach((insight) => {
          expect(insight.confidence).toBeGreaterThanOrEqual(0.8);
        });
      }
    });
  });

  describe('Alerts', () => {
    it('should create and delete alert', async () => {
      // Create alert
      const alert = await client.alerts.create({
        signalType: 'mempool',
        threshold: 100.0,
        operator: 'gt',
      });
      expect(alert.id).toBeDefined();
      expect(alert.signalType).toBe('mempool');

      // Delete alert
      const result = await client.alerts.delete(alert.id);
      expect(result).toBe(true);
    });

    it('should list alerts', async () => {
      const alerts = await client.alerts.list();
      expect(Array.isArray(alerts)).toBe(true);
    });

    it('should update alert', async () => {
      // Create alert first
      const alert = await client.alerts.create({
        signalType: 'exchange',
        threshold: 500.0,
        operator: 'gt',
      });

      // Update it
      const updated = await client.alerts.update(alert.id, {
        threshold: 750.0,
        isActive: false,
      });
      expect(updated.threshold).toBe(750.0);
      expect(updated.isActive).toBe(false);

      // Clean up
      await client.alerts.delete(alert.id);
    });
  });

  describe('Daily Brief', () => {
    it('should get latest daily brief', async () => {
      const brief = await client.dailyBrief.getLatest();
      expect(brief.date).toBeDefined();
      expect(Array.isArray(brief.insights)).toBe(true);
    });

    it('should get daily brief by date', async () => {
      const today = new Date();
      const brief = await client.dailyBrief.getByDate(today);
      expect(brief.date).toBeDefined();
    });
  });

  describe('Feedback', () => {
    it('should get accuracy leaderboard', async () => {
      const leaderboard = await client.feedback.getAccuracyLeaderboard();
      expect(Array.isArray(leaderboard)).toBe(true);
      if (leaderboard.length > 0) {
        expect(leaderboard[0]).toHaveProperty('modelVersion');
        expect(leaderboard[0]).toHaveProperty('accuracyRating');
      }
    });
  });

  describe('Error Handling', () => {
    it('should throw AuthenticationError with invalid API key', async () => {
      const invalidClient = new UtxoIQClient({ apiKey: 'invalid-key' });
      await expect(invalidClient.insights.getLatest()).rejects.toThrow(
        AuthenticationError
      );
    });

    it('should throw NotFoundError for nonexistent resource', async () => {
      await expect(
        client.insights.getById('nonexistent-id-12345')
      ).rejects.toThrow(NotFoundError);
    });
  });
});

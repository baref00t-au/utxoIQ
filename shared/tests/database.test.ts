/**
 * Unit tests for database utilities and query builders
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { BigQueryInsightBuilder, BigQuerySignalBuilder, PostgresAlertBuilder } from '../utils/database';

describe('BigQueryInsightBuilder', () => {
  let builder: BigQueryInsightBuilder;

  beforeEach(() => {
    builder = new BigQueryInsightBuilder();
  });

  it('should build basic query', () => {
    const query = builder.build();
    expect(query).toContain('SELECT * FROM');
    expect(query).toContain('intel.insights');
    expect(query).toContain('ORDER BY created_at DESC');
    expect(query).toContain('LIMIT 20');
  });

  it('should add signal type filter', () => {
    const query = builder.whereSignalType('mempool').build();
    expect(query).toContain("signal_type = 'mempool'");
  });

  it('should add confidence filter', () => {
    const query = builder.whereConfidenceGreaterThan(0.7).build();
    expect(query).toContain('confidence >= 0.7');
  });

  it('should chain multiple filters', () => {
    const query = builder
      .whereSignalType('exchange')
      .whereConfidenceGreaterThan(0.8)
      .whereBlockHeightGreaterThan(800000)
      .limit(50)
      .build();

    expect(query).toContain("signal_type = 'exchange'");
    expect(query).toContain('confidence >= 0.8');
    expect(query).toContain('block_height > 800000');
    expect(query).toContain('LIMIT 50');
  });

  it('should add timestamp filter', () => {
    const date = new Date('2024-01-01T00:00:00Z');
    const query = builder.whereTimestampAfter(date).build();
    expect(query).toContain('created_at > TIMESTAMP');
    expect(query).toContain('2024-01-01');
  });
});

describe('BigQuerySignalBuilder', () => {
  let builder: BigQuerySignalBuilder;

  beforeEach(() => {
    builder = new BigQuerySignalBuilder();
  });

  it('should build basic signal query', () => {
    const query = builder.build();
    expect(query).toContain('SELECT * FROM');
    expect(query).toContain('intel.signals');
    expect(query).toContain('ORDER BY processed_at DESC');
  });

  it('should filter by signal type', () => {
    const query = builder.whereType('whale').build();
    expect(query).toContain("type = 'whale'");
  });

  it('should filter by block height', () => {
    const query = builder.whereBlockHeight(800000).build();
    expect(query).toContain('block_height = 800000');
  });

  it('should filter by strength', () => {
    const query = builder.whereStrengthGreaterThan(0.5).build();
    expect(query).toContain('strength >= 0.5');
  });
});

describe('PostgresAlertBuilder', () => {
  let builder: PostgresAlertBuilder;

  beforeEach(() => {
    builder = new PostgresAlertBuilder();
  });

  it('should build basic alert query', () => {
    const { query, params } = builder.build();
    expect(query).toContain('SELECT * FROM user_alerts');
    expect(query).toContain('ORDER BY created_at DESC');
    expect(params).toEqual([]);
  });

  it('should filter by user ID', () => {
    const { query, params } = builder.whereUserId('user123').build();
    expect(query).toContain('user_id = $1');
    expect(params).toEqual(['user123']);
  });

  it('should filter by active status', () => {
    const { query, params } = builder.whereIsActive(true).build();
    expect(query).toContain('is_active = $1');
    expect(params).toEqual([true]);
  });

  it('should chain multiple filters with correct parameter numbering', () => {
    const { query, params } = builder
      .whereUserId('user123')
      .whereIsActive(true)
      .whereSignalType('mempool')
      .build();

    expect(query).toContain('user_id = $1');
    expect(query).toContain('is_active = $2');
    expect(query).toContain('signal_type = $3');
    expect(params).toEqual(['user123', true, 'mempool']);
  });
});

/**
 * Tests for error handling
 */

import { describe, it, expect } from 'vitest';
import {
  UtxoIQError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  NotFoundError,
  SubscriptionRequiredError,
  DataUnavailableError,
  ConfidenceTooLowError,
} from '../errors';

describe('Error Classes', () => {
  it('should create UtxoIQError with all properties', () => {
    const error = new UtxoIQError(
      'Test error',
      500,
      'TEST_ERROR',
      { detail: 'test' },
      'req_123'
    );

    expect(error.message).toBe('Test error');
    expect(error.statusCode).toBe(500);
    expect(error.errorCode).toBe('TEST_ERROR');
    expect(error.details).toEqual({ detail: 'test' });
    expect(error.requestId).toBe('req_123');
    expect(error.name).toBe('UtxoIQError');
  });

  it('should create AuthenticationError', () => {
    const error = new AuthenticationError('Auth failed', 401);
    expect(error).toBeInstanceOf(UtxoIQError);
    expect(error).toBeInstanceOf(AuthenticationError);
    expect(error.name).toBe('AuthenticationError');
    expect(error.statusCode).toBe(401);
  });

  it('should create RateLimitError with retry after', () => {
    const error = new RateLimitError('Rate limit exceeded', 60, 429);
    expect(error).toBeInstanceOf(UtxoIQError);
    expect(error).toBeInstanceOf(RateLimitError);
    expect(error.name).toBe('RateLimitError');
    expect(error.retryAfter).toBe(60);
    expect(error.statusCode).toBe(429);
  });

  it('should create ValidationError', () => {
    const error = new ValidationError('Invalid input', 400);
    expect(error).toBeInstanceOf(UtxoIQError);
    expect(error).toBeInstanceOf(ValidationError);
    expect(error.name).toBe('ValidationError');
  });

  it('should create NotFoundError', () => {
    const error = new NotFoundError('Resource not found', 404);
    expect(error).toBeInstanceOf(UtxoIQError);
    expect(error).toBeInstanceOf(NotFoundError);
    expect(error.name).toBe('NotFoundError');
  });

  it('should create SubscriptionRequiredError', () => {
    const error = new SubscriptionRequiredError('Subscription required', 402);
    expect(error).toBeInstanceOf(UtxoIQError);
    expect(error).toBeInstanceOf(SubscriptionRequiredError);
    expect(error.name).toBe('SubscriptionRequiredError');
  });

  it('should create DataUnavailableError', () => {
    const error = new DataUnavailableError('Data not available', 503);
    expect(error).toBeInstanceOf(UtxoIQError);
    expect(error).toBeInstanceOf(DataUnavailableError);
    expect(error.name).toBe('DataUnavailableError');
  });

  it('should create ConfidenceTooLowError', () => {
    const error = new ConfidenceTooLowError('Confidence too low', 422);
    expect(error).toBeInstanceOf(UtxoIQError);
    expect(error).toBeInstanceOf(ConfidenceTooLowError);
    expect(error.name).toBe('ConfidenceTooLowError');
  });

  it('should preserve error stack trace', () => {
    const error = new UtxoIQError('Test error');
    expect(error.stack).toBeDefined();
  });
});

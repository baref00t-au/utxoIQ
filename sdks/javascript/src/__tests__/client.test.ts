/**
 * Tests for utxoIQ client
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { UtxoIQClient } from '../client';
import {
  AuthenticationError,
  RateLimitError,
  ValidationError,
  NotFoundError,
} from '../errors';

vi.mock('axios');
const mockedAxios = axios as any;

describe('UtxoIQClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.create.mockReturnValue({
      defaults: { headers: { common: {} } },
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    });
  });

  it('should initialize with Firebase token', () => {
    const client = new UtxoIQClient({ firebaseToken: 'test-token' });
    expect(client).toBeDefined();
    expect(client.insights).toBeDefined();
  });

  it('should initialize with API key', () => {
    const client = new UtxoIQClient({ apiKey: 'test-api-key' });
    expect(client).toBeDefined();
    expect(client.alerts).toBeDefined();
  });

  it('should initialize without authentication (Guest Mode)', () => {
    const client = new UtxoIQClient();
    expect(client).toBeDefined();
    expect(client.insights).toBeDefined();
  });

  it('should use custom base URL', () => {
    const client = new UtxoIQClient({ baseUrl: 'https://custom.api.com' });
    expect(client).toBeDefined();
  });

  it('should have all resource endpoints', () => {
    const client = new UtxoIQClient({ apiKey: 'test-key' });
    expect(client.insights).toBeDefined();
    expect(client.alerts).toBeDefined();
    expect(client.feedback).toBeDefined();
    expect(client.dailyBrief).toBeDefined();
    expect(client.chat).toBeDefined();
    expect(client.billing).toBeDefined();
    expect(client.emailPreferences).toBeDefined();
  });
});

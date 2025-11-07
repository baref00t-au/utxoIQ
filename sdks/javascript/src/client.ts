/**
 * Main client for utxoIQ API
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import type { ClientConfig } from './types';
import {
  UtxoIQError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  NotFoundError,
  SubscriptionRequiredError,
  DataUnavailableError,
  ConfidenceTooLowError,
} from './errors';
import { InsightsResource } from './resources/insights';
import { AlertsResource } from './resources/alerts';
import { FeedbackResource } from './resources/feedback';
import { DailyBriefResource } from './resources/dailyBrief';
import { ChatResource } from './resources/chat';
import { BillingResource } from './resources/billing';
import { EmailPreferencesResource } from './resources/emailPreferences';

export class UtxoIQClient {
  private axiosInstance: AxiosInstance;
  public readonly insights: InsightsResource;
  public readonly alerts: AlertsResource;
  public readonly feedback: FeedbackResource;
  public readonly dailyBrief: DailyBriefResource;
  public readonly chat: ChatResource;
  public readonly billing: BillingResource;
  public readonly emailPreferences: EmailPreferencesResource;

  constructor(config: ClientConfig = {}) {
    const {
      firebaseToken,
      apiKey,
      baseUrl = 'https://api.utxoiq.com',
      timeout = 30000,
      maxRetries = 3,
      retryDelay = 1000,
    } = config;

    // Create axios instance
    this.axiosInstance = axios.create({
      baseURL: baseUrl,
      timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'utxoiq-javascript-sdk/1.0.0',
      },
    });

    // Set authentication headers
    if (firebaseToken) {
      this.axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${firebaseToken}`;
    } else if (apiKey) {
      this.axiosInstance.defaults.headers.common['X-API-Key'] = apiKey;
    }

    // Add response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response) {
          this.handleErrorResponse(error);
        } else if (error.code === 'ECONNABORTED') {
          throw new UtxoIQError('Request timeout');
        } else if (error.message === 'Network Error') {
          throw new UtxoIQError('Network error');
        }
        throw new UtxoIQError(`Request failed: ${error.message}`);
      }
    );

    // Add retry interceptor
    this.axiosInstance.interceptors.response.use(undefined, async (error) => {
      const config = error.config as AxiosRequestConfig & { _retryCount?: number };
      
      if (!config || !config._retryCount) {
        config._retryCount = 0;
      }

      const shouldRetry =
        config._retryCount < maxRetries &&
        error.response &&
        [429, 500, 502, 503, 504].includes(error.response.status);

      if (shouldRetry) {
        config._retryCount += 1;
        const delay = retryDelay * Math.pow(2, config._retryCount - 1);
        await new Promise((resolve) => setTimeout(resolve, delay));
        return this.axiosInstance(config);
      }

      return Promise.reject(error);
    });

    // Initialize resource endpoints
    this.insights = new InsightsResource(this.axiosInstance);
    this.alerts = new AlertsResource(this.axiosInstance);
    this.feedback = new FeedbackResource(this.axiosInstance);
    this.dailyBrief = new DailyBriefResource(this.axiosInstance);
    this.chat = new ChatResource(this.axiosInstance);
    this.billing = new BillingResource(this.axiosInstance);
    this.emailPreferences = new EmailPreferencesResource(this.axiosInstance);
  }

  private handleErrorResponse(error: AxiosError): never {
    const response = error.response;
    if (!response) {
      throw new UtxoIQError('Unknown error');
    }

    let message = 'Unknown error';
    let errorCode: string | undefined;
    let details: any;
    let requestId: string | undefined;

    if (response.data && typeof response.data === 'object') {
      const errorData = response.data as any;
      const errorInfo = errorData.error || {};
      message = errorInfo.message || message;
      errorCode = errorInfo.code;
      details = errorInfo.details;
      requestId = errorData.request_id;
    }

    const statusCode = response.status;

    // Map status codes to exception types
    if (statusCode === 401) {
      throw new AuthenticationError(message, statusCode, errorCode, details, requestId);
    } else if (statusCode === 429) {
      const retryAfter = details?.retry_after;
      throw new RateLimitError(message, retryAfter, statusCode, errorCode, details, requestId);
    } else if (statusCode === 400) {
      throw new ValidationError(message, statusCode, errorCode, details, requestId);
    } else if (statusCode === 404) {
      throw new NotFoundError(message, statusCode, errorCode, details, requestId);
    } else if (statusCode === 402) {
      throw new SubscriptionRequiredError(message, statusCode, errorCode, details, requestId);
    } else if (statusCode === 503 && errorCode === 'DATA_UNAVAILABLE') {
      throw new DataUnavailableError(message, statusCode, errorCode, details, requestId);
    } else if (statusCode === 422 && errorCode === 'CONFIDENCE_TOO_LOW') {
      throw new ConfidenceTooLowError(message, statusCode, errorCode, details, requestId);
    } else {
      throw new UtxoIQError(message, statusCode, errorCode, details, requestId);
    }
  }
}

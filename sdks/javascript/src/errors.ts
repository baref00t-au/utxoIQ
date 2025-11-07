/**
 * Error classes for utxoIQ SDK
 */

export interface ErrorDetails {
  [key: string]: any;
}

export class UtxoIQError extends Error {
  public readonly statusCode?: number;
  public readonly errorCode?: string;
  public readonly details?: ErrorDetails;
  public readonly requestId?: string;

  constructor(
    message: string,
    statusCode?: number,
    errorCode?: string,
    details?: ErrorDetails,
    requestId?: string
  ) {
    super(message);
    this.name = 'UtxoIQError';
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.details = details;
    this.requestId = requestId;
    Object.setPrototypeOf(this, UtxoIQError.prototype);
  }
}

export class AuthenticationError extends UtxoIQError {
  constructor(
    message: string,
    statusCode?: number,
    errorCode?: string,
    details?: ErrorDetails,
    requestId?: string
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'AuthenticationError';
    Object.setPrototypeOf(this, AuthenticationError.prototype);
  }
}

export class RateLimitError extends UtxoIQError {
  public readonly retryAfter?: number;

  constructor(
    message: string,
    retryAfter?: number,
    statusCode?: number,
    errorCode?: string,
    details?: ErrorDetails,
    requestId?: string
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
    Object.setPrototypeOf(this, RateLimitError.prototype);
  }
}

export class ValidationError extends UtxoIQError {
  constructor(
    message: string,
    statusCode?: number,
    errorCode?: string,
    details?: ErrorDetails,
    requestId?: string
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

export class NotFoundError extends UtxoIQError {
  constructor(
    message: string,
    statusCode?: number,
    errorCode?: string,
    details?: ErrorDetails,
    requestId?: string
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'NotFoundError';
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}

export class SubscriptionRequiredError extends UtxoIQError {
  constructor(
    message: string,
    statusCode?: number,
    errorCode?: string,
    details?: ErrorDetails,
    requestId?: string
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'SubscriptionRequiredError';
    Object.setPrototypeOf(this, SubscriptionRequiredError.prototype);
  }
}

export class DataUnavailableError extends UtxoIQError {
  constructor(
    message: string,
    statusCode?: number,
    errorCode?: string,
    details?: ErrorDetails,
    requestId?: string
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'DataUnavailableError';
    Object.setPrototypeOf(this, DataUnavailableError.prototype);
  }
}

export class ConfidenceTooLowError extends UtxoIQError {
  constructor(
    message: string,
    statusCode?: number,
    errorCode?: string,
    details?: ErrorDetails,
    requestId?: string
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'ConfidenceTooLowError';
    Object.setPrototypeOf(this, ConfidenceTooLowError.prototype);
  }
}

/**
 * Type definitions for utxoIQ SDK
 */

export interface Citation {
  type: string;
  id: string;
  description: string;
  url: string;
}

export interface ExplainabilitySummary {
  confidenceFactors: {
    [key: string]: number;
  };
  explanation: string;
  supportingEvidence: string[];
}

export interface Insight {
  id: string;
  signalType: string;
  headline: string;
  summary: string;
  confidence: number;
  timestamp: string;
  blockHeight: number;
  evidence: Citation[];
  chartUrl?: string;
  tags: string[];
  explainability?: ExplainabilitySummary;
  accuracyRating?: number;
  isPredictive: boolean;
}

export interface Alert {
  id: string;
  userId: string;
  signalType: string;
  threshold: number;
  operator: string;
  isActive: boolean;
  createdAt: string;
  notificationChannel?: string;
}

export interface DailyBrief {
  date: string;
  insights: Insight[];
  summary: string;
  createdAt: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  timestamp: string;
}

export interface UserFeedback {
  insightId: string;
  userId: string;
  rating: string;
  timestamp: string;
  comment?: string;
}

export interface AccuracyLeaderboard {
  modelVersion: string;
  accuracyRating: number;
  totalRatings: number;
  usefulCount: number;
  notUsefulCount: number;
}

export interface Subscription {
  userId: string;
  tier: string;
  status: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
}

export interface EmailPreferences {
  userId: string;
  dailyBriefEnabled: boolean;
  frequency: string;
  signalFilters: string[];
  quietHours?: {
    start: string;
    end: string;
  };
}

export interface ClientConfig {
  firebaseToken?: string;
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
  retryDelay?: number;
}

export interface GetLatestInsightsParams {
  limit?: number;
  category?: string;
  minConfidence?: number;
}

export interface GetPublicInsightsParams {
  limit?: number;
}

export interface SearchInsightsParams {
  query: string;
  limit?: number;
  category?: string;
}

export interface CreateAlertParams {
  signalType: string;
  threshold: number;
  operator: string;
  notificationChannel?: string;
  isActive?: boolean;
}

export interface UpdateAlertParams {
  threshold?: number;
  isActive?: boolean;
  notificationChannel?: string;
}

export interface SubmitFeedbackParams {
  insightId: string;
  rating: string;
  comment?: string;
}

export interface ChatQueryParams {
  question: string;
}

export interface UpdateEmailPreferencesParams {
  dailyBriefEnabled?: boolean;
  frequency?: string;
  signalFilters?: string[];
  quietHours?: {
    start: string;
    end: string;
  };
}

export interface CreateCheckoutSessionParams {
  tier: string;
  successUrl: string;
  cancelUrl: string;
}

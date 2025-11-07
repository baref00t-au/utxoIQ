/**
 * Core TypeScript interfaces and data models for utxoIQ platform
 * Shared between frontend and backend services
 */

export type SignalType = 'mempool' | 'exchange' | 'miner' | 'whale' | 'predictive';

export type CitationType = 'block' | 'transaction' | 'address';

export type AlertOperator = 'gt' | 'lt' | 'eq';

export type FeedbackRating = 'useful' | 'not_useful';

export type EmailFrequency = 'daily' | 'weekly' | 'never';

export type SLATier = 'standard' | 'premium';

export type PredictiveSignalType = 'fee_forecast' | 'liquidity_pressure';

/**
 * Citation interface for blockchain evidence
 */
export interface Citation {
  type: CitationType;
  id: string;
  description: string;
  url: string;
}

/**
 * Core Insight interface representing AI-generated blockchain insights
 */
export interface Insight {
  id: string;
  signal_type: SignalType;
  headline: string;
  summary: string;
  confidence: number; // 0-1
  timestamp: Date;
  block_height: number;
  evidence: Citation[];
  chart_url?: string;
  tags: string[];
  explainability?: ExplainabilitySummary;
  accuracy_rating?: number;
  is_predictive?: boolean;
}

/**
 * Signal interface for blockchain events and patterns
 */
export interface Signal {
  type: SignalType;
  strength: number;
  data: Record<string, any>;
  block_height: number;
  transaction_ids: string[];
  entity_ids: string[];
  is_predictive?: boolean;
  prediction_confidence_interval?: [number, number];
}

/**
 * Alert interface for user-defined threshold monitoring
 */
export interface Alert {
  id: string;
  user_id: string;
  signal_type: SignalType;
  threshold: number;
  operator: AlertOperator;
  is_active: boolean;
  created_at: Date;
}

/**
 * v2: Explainability Summary for confidence score transparency
 */
export interface ExplainabilitySummary {
  confidence_factors: {
    signal_strength: number;
    historical_accuracy: number;
    data_quality: number;
  };
  explanation: string;
  supporting_evidence: string[];
}

/**
 * v2: User Feedback for insight accuracy ratings
 */
export interface UserFeedback {
  insight_id: string;
  user_id: string;
  rating: FeedbackRating;
  timestamp: Date;
  comment?: string;
}

/**
 * v2: Predictive Signal for forecasting capabilities
 */
export interface PredictiveSignal {
  type: PredictiveSignalType;
  prediction: number;
  confidence_interval: [number, number];
  forecast_horizon: string;
  model_version: string;
}

/**
 * v2: Email Preferences for customizable notifications
 */
export interface EmailPreferences {
  user_id: string;
  daily_brief_enabled: boolean;
  frequency: EmailFrequency;
  signal_filters: SignalType[];
  quiet_hours?: {
    start: string;
    end: string;
  };
}

/**
 * v2: White-Label Configuration for enterprise clients
 */
export interface WhiteLabelConfig {
  client_id: string;
  custom_domain: string;
  branding: {
    logo_url: string;
    primary_color: string;
    company_name: string;
  };
  api_endpoint_prefix: string;
  sla_tier: SLATier;
}

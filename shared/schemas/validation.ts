/**
 * Zod validation schemas for utxoIQ data models
 * Provides runtime type validation and parsing
 */

import { z } from 'zod';

// Enum schemas
export const SignalTypeSchema = z.enum(['mempool', 'exchange', 'miner', 'whale', 'predictive']);

export const CitationTypeSchema = z.enum(['block', 'transaction', 'address']);

export const AlertOperatorSchema = z.enum(['gt', 'lt', 'eq']);

export const FeedbackRatingSchema = z.enum(['useful', 'not_useful']);

export const EmailFrequencySchema = z.enum(['daily', 'weekly', 'never']);

export const SLATierSchema = z.enum(['standard', 'premium']);

export const PredictiveSignalTypeSchema = z.enum(['fee_forecast', 'liquidity_pressure']);

// Citation schema
export const CitationSchema = z.object({
  type: CitationTypeSchema,
  id: z.string().min(1),
  description: z.string().min(1),
  url: z.string().url(),
});

// Insight schema
export const InsightSchema = z.object({
  id: z.string().uuid(),
  signal_type: SignalTypeSchema,
  headline: z.string().min(1).max(280),
  summary: z.string().min(1),
  confidence: z.number().min(0).max(1),
  timestamp: z.date(),
  block_height: z.number().int().positive(),
  evidence: z.array(CitationSchema),
  chart_url: z.string().url().optional(),
  tags: z.array(z.string()),
  explainability: z.object({
    confidence_factors: z.object({
      signal_strength: z.number().min(0).max(1),
      historical_accuracy: z.number().min(0).max(1),
      data_quality: z.number().min(0).max(1),
    }),
    explanation: z.string(),
    supporting_evidence: z.array(z.string()),
  }).optional(),
  accuracy_rating: z.number().min(0).max(1).optional(),
  is_predictive: z.boolean().optional(),
});

// Signal schema
export const SignalSchema = z.object({
  type: SignalTypeSchema,
  strength: z.number().min(0).max(1),
  data: z.record(z.any()),
  block_height: z.number().int().positive(),
  transaction_ids: z.array(z.string()),
  entity_ids: z.array(z.string()),
  is_predictive: z.boolean().optional(),
  prediction_confidence_interval: z.tuple([z.number(), z.number()]).optional(),
});

// Alert schema
export const AlertSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().min(1),
  signal_type: SignalTypeSchema,
  threshold: z.number(),
  operator: AlertOperatorSchema,
  is_active: z.boolean(),
  created_at: z.date(),
});

// v2: Explainability Summary schema
export const ExplainabilitySummarySchema = z.object({
  confidence_factors: z.object({
    signal_strength: z.number().min(0).max(1),
    historical_accuracy: z.number().min(0).max(1),
    data_quality: z.number().min(0).max(1),
  }),
  explanation: z.string().min(1),
  supporting_evidence: z.array(z.string()),
});

// v2: User Feedback schema
export const UserFeedbackSchema = z.object({
  insight_id: z.string().uuid(),
  user_id: z.string().min(1),
  rating: FeedbackRatingSchema,
  timestamp: z.date(),
  comment: z.string().optional(),
});

// v2: Predictive Signal schema
export const PredictiveSignalSchema = z.object({
  type: PredictiveSignalTypeSchema,
  prediction: z.number(),
  confidence_interval: z.tuple([z.number(), z.number()]),
  forecast_horizon: z.string().min(1),
  model_version: z.string().min(1),
});

// v2: Email Preferences schema
export const EmailPreferencesSchema = z.object({
  user_id: z.string().min(1),
  daily_brief_enabled: z.boolean(),
  frequency: EmailFrequencySchema,
  signal_filters: z.array(SignalTypeSchema),
  quiet_hours: z.object({
    start: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/),
    end: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/),
  }).optional(),
});

// v2: White-Label Config schema
export const WhiteLabelConfigSchema = z.object({
  client_id: z.string().uuid(),
  custom_domain: z.string().min(1),
  branding: z.object({
    logo_url: z.string().url(),
    primary_color: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    company_name: z.string().min(1),
  }),
  api_endpoint_prefix: z.string().min(1),
  sla_tier: SLATierSchema,
});

// Export type inference helpers
export type InsightInput = z.infer<typeof InsightSchema>;
export type SignalInput = z.infer<typeof SignalSchema>;
export type AlertInput = z.infer<typeof AlertSchema>;
export type UserFeedbackInput = z.infer<typeof UserFeedbackSchema>;
export type PredictiveSignalInput = z.infer<typeof PredictiveSignalSchema>;
export type EmailPreferencesInput = z.infer<typeof EmailPreferencesSchema>;
export type WhiteLabelConfigInput = z.infer<typeof WhiteLabelConfigSchema>;

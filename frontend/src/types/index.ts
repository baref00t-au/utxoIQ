export type SignalType = 'mempool' | 'exchange' | 'miner' | 'whale';

export interface Citation {
  type: 'block' | 'transaction' | 'address';
  id: string;
  description: string;
  url: string;
}

export interface ExplainabilitySummary {
  confidence_factors: {
    signal_strength: number;
    historical_accuracy: number;
    data_quality: number;
  };
  explanation: string;
  supporting_evidence: string[];
}

export interface Insight {
  id: string;
  signal_type: SignalType;
  headline: string;
  summary: string;
  confidence: number;
  timestamp: string;
  block_height: number;
  evidence: Citation[];
  chart_url?: string;
  tags: string[];
  explainability?: ExplainabilitySummary;
  accuracy_rating?: number;
  is_predictive?: boolean;
}

export interface Alert {
  id: string;
  user_id: string;
  signal_type: SignalType;
  threshold: number;
  operator: 'gt' | 'lt' | 'eq';
  is_active: boolean;
  created_at: string;
}

export interface UserFeedback {
  insight_id: string;
  user_id: string;
  rating: 'useful' | 'not_useful';
  timestamp: string;
  comment?: string;
}

export interface DailyBrief {
  date: string;
  insights: Insight[];
  summary: string;
}

export type SignalType = 'mempool' | 'exchange' | 'miner' | 'whale';

export interface FilterState {
  search: string;
  categories: SignalType[];
  minConfidence: number;
  dateRange: { start: Date; end: Date } | null;
}

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

// Monitoring types
export interface MetricDataPoint {
  timestamp: string;
  value: number;
}

export interface BaselineStats {
  mean: number;
  median: number;
  std_dev: number;
  p95: number;
  p99: number;
}

export interface ServiceMetrics {
  cpu_usage: MetricDataPoint[];
  memory_usage: MetricDataPoint[];
  response_time: MetricDataPoint[];
  error_rate: MetricDataPoint[];
}

export interface AlertConfiguration {
  id: string;
  name: string;
  service_name: string;
  metric_type: string;
  threshold_type: 'absolute' | 'percentage' | 'rate';
  threshold_value: number;
  comparison_operator: '>' | '<' | '>=' | '<=' | '==';
  severity: 'info' | 'warning' | 'critical';
  evaluation_window_seconds: number;
  notification_channels: ('email' | 'slack' | 'sms')[];
  enabled: boolean;
  created_at: string;
}

export interface AlertHistoryItem {
  id: string;
  triggered_at: string;
  resolved_at?: string;
  severity: 'info' | 'warning' | 'critical';
  metric_value: number;
  threshold_value: number;
  message: string;
  notification_sent: boolean;
}

export interface ServiceNode {
  id: string;
  name: string;
  health_status: 'healthy' | 'degraded' | 'down';
  cpu_usage?: number;
  memory_usage?: number;
}

export interface ServiceEdge {
  source: string;
  target: string;
  request_count: number;
  error_rate: number;
  avg_latency: number;
}

export interface DependencyGraph {
  nodes: ServiceNode[];
  edges: ServiceEdge[];
}

export interface LogEntry {
  id: string;
  timestamp: string;
  severity: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  service: string;
  message: string;
  metadata?: Record<string, any>;
}

export interface TraceSpan {
  span_id: string;
  parent_span_id?: string;
  name: string;
  start_time: string;
  end_time: string;
  duration_ms: number;
  status: 'ok' | 'error';
  attributes?: Record<string, any>;
}

export interface Trace {
  trace_id: string;
  spans: TraceSpan[];
  total_duration_ms: number;
}

export interface DashboardWidget {
  id: string;
  type: 'line_chart' | 'bar_chart' | 'gauge' | 'stat_card';
  title: string;
  data_source: {
    metric_type: string;
    aggregation: string;
    time_range: string;
  };
  display_options: Record<string, any>;
  position: { x: number; y: number; w: number; h: number };
}

export interface DashboardConfiguration {
  id: string;
  name: string;
  widgets: DashboardWidget[];
  is_public: boolean;
  share_token?: string;
  created_at: string;
  updated_at: string;
}

export interface FilterPreset {
  id: string;
  user_id: string;
  name: string;
  filters: FilterState;
  created_at: string;
  updated_at: string;
}

export interface BookmarkFolder {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  bookmark_count?: number;
}

export interface Bookmark {
  id: string;
  user_id: string;
  insight_id: string;
  folder_id?: string;
  note?: string;
  created_at: string;
  updated_at: string;
}

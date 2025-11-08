'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Activity, AlertCircle, CheckCircle, Clock, TrendingUp, Wifi, WifiOff } from 'lucide-react';
import { useMonitoringWebSocket } from '@/hooks/use-monitoring-websocket';
import { toast } from '@/lib/toast';

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  last_check: string;
  response_time_ms?: number;
  error_message?: string;
}

interface BackfillProgress {
  job_id: string;
  status: 'running' | 'paused' | 'completed' | 'failed';
  start_block: number;
  end_block: number;
  current_block: number;
  blocks_processed: number;
  blocks_remaining: number;
  progress_percent: number;
  rate_blocks_per_sec: number;
  estimated_completion?: string;
  started_at: string;
  updated_at: string;
  error_count: number;
}

interface ProcessingMetrics {
  blocks_processed_24h: number;
  insights_generated_24h: number;
  signals_computed_24h: number;
  avg_block_processing_time_ms: number;
  avg_insight_generation_time_ms: number;
  current_block_height: number;
  last_processed_block: number;
  blocks_behind: number;
}

interface SystemStatus {
  status: 'healthy' | 'degraded' | 'down';
  services: ServiceHealth[];
  backfill_jobs: BackfillProgress[];
  processing_metrics: ProcessingMetrics;
  timestamp: string;
}

export function SystemStatusDashboard() {
  const { data: status, isLoading } = useQuery<SystemStatus>({
    queryKey: ['system-status'],
    queryFn: async () => {
      const res = await fetch('/api/v1/monitoring/status');
      if (!res.ok) throw new Error('Failed to fetch status');
      return res.json();
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Connect to WebSocket for real-time updates
  const { isConnected } = useMonitoringWebSocket({
    enabled: true,
    onInsightGenerated: (data) => {
      toast.success('New insight generated!', {
        description: data.headline || 'Check the insights feed',
      });
    },
    onBackfillUpdate: (jobId, data) => {
      // Updates are handled automatically via query invalidation
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center">
              <Activity className="h-6 w-6 animate-spin" />
              <span className="ml-2">Loading system status...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!status) return null;

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                System Status
                <span title={isConnected ? "Live updates connected" : "Live updates disconnected"}>
                  {isConnected ? (
                    <Wifi className="h-4 w-4 text-green-500" />
                  ) : (
                    <WifiOff className="h-4 w-4 text-gray-400" />
                  )}
                </span>
              </CardTitle>
              <CardDescription>Real-time platform health</CardDescription>
            </div>
            <StatusBadge status={status.status} />
          </div>
        </CardHeader>
      </Card>

      {/* Services Health */}
      <Card>
        <CardHeader>
          <CardTitle>Services</CardTitle>
          <CardDescription>Microservices health status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {status.services.map((service) => (
              <div
                key={service.name}
                className="flex items-center justify-between p-3 rounded-lg border"
              >
                <div className="flex items-center gap-3">
                  <StatusIcon status={service.status} />
                  <div>
                    <p className="font-medium">{service.name}</p>
                    {service.response_time_ms && (
                      <p className="text-sm text-muted-foreground">
                        {service.response_time_ms.toFixed(1)}ms
                      </p>
                    )}
                  </div>
                </div>
                <StatusBadge status={service.status} />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Backfill Progress */}
      {status.backfill_jobs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Backfill Progress</CardTitle>
            <CardDescription>Historical data ingestion</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {status.backfill_jobs.map((job) => (
                <div key={job.job_id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">
                        Blocks {job.start_block.toLocaleString()} - {job.end_block.toLocaleString()}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {job.rate_blocks_per_sec.toFixed(1)} blocks/sec
                      </p>
                    </div>
                    <Badge variant={job.status === 'running' ? 'default' : 'secondary'}>
                      {job.status}
                    </Badge>
                  </div>
                  <Progress value={job.progress_percent} />
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>{job.blocks_processed.toLocaleString()} processed</span>
                    <span>{job.blocks_remaining.toLocaleString()} remaining</span>
                  </div>
                  {job.estimated_completion && (
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      ETA: {new Date(job.estimated_completion).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Processing Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Blocks (24h)"
          value={status.processing_metrics.blocks_processed_24h}
          icon={<Activity className="h-4 w-4" />}
        />
        <MetricCard
          title="Insights (24h)"
          value={status.processing_metrics.insights_generated_24h}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <MetricCard
          title="Signals (24h)"
          value={status.processing_metrics.signals_computed_24h}
          icon={<Activity className="h-4 w-4" />}
        />
        <MetricCard
          title="Blocks Behind"
          value={status.processing_metrics.blocks_behind}
          icon={<Clock className="h-4 w-4" />}
          warning={status.processing_metrics.blocks_behind > 5}
        />
      </div>

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Performance</CardTitle>
          <CardDescription>Average processing times</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm">Block Processing</span>
              <span className="font-mono text-sm">
                {status.processing_metrics.avg_block_processing_time_ms.toFixed(0)}ms
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Insight Generation</span>
              <span className="font-mono text-sm">
                {status.processing_metrics.avg_insight_generation_time_ms.toFixed(0)}ms
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, 'default' | 'secondary' | 'destructive'> = {
    healthy: 'default',
    degraded: 'secondary',
    down: 'destructive',
    running: 'default',
    paused: 'secondary',
    completed: 'default',
    failed: 'destructive',
  };

  return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>;
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'healthy') {
    return <CheckCircle className="h-5 w-5 text-green-500" />;
  }
  if (status === 'degraded') {
    return <AlertCircle className="h-5 w-5 text-yellow-500" />;
  }
  return <AlertCircle className="h-5 w-5 text-red-500" />;
}

function MetricCard({
  title,
  value,
  icon,
  warning = false,
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
  warning?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${warning ? 'text-yellow-500' : ''}`}>
          {value.toLocaleString()}
        </div>
      </CardContent>
    </Card>
  );
}

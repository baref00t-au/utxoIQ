'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { fetchServiceMetrics, fetchBaseline } from '@/lib/api';
import { Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react';

const TIME_RANGES = [
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '24h', label: '24 Hours' },
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
];

const SERVICES = [
  { value: 'web-api', label: 'Web API' },
  { value: 'feature-engine', label: 'Feature Engine' },
  { value: 'insight-generator', label: 'Insight Generator' },
  { value: 'chart-renderer', label: 'Chart Renderer' },
  { value: 'data-ingestion', label: 'Data Ingestion' },
];

const METRICS = [
  { key: 'cpu_usage', label: 'CPU Usage', unit: '%', color: 'hsl(var(--brand))' },
  { key: 'memory_usage', label: 'Memory Usage', unit: '%', color: 'hsl(var(--exchange))' },
  { key: 'response_time', label: 'Response Time', unit: 'ms', color: 'hsl(var(--miner))' },
  { key: 'error_rate', label: 'Error Rate', unit: '%', color: 'hsl(var(--destructive))' },
];

export function MetricsDashboard() {
  const [selectedService, setSelectedService] = useState('web-api');
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedMetric, setSelectedMetric] = useState('cpu_usage');

  const { data: metricsData, isLoading: metricsLoading } = useQuery({
    queryKey: ['service-metrics', selectedService, timeRange],
    queryFn: () => fetchServiceMetrics(selectedService, timeRange),
    refetchInterval: 60000, // Refresh every minute
  });

  const { data: baselineData, isLoading: baselineLoading } = useQuery({
    queryKey: ['baseline', selectedService, selectedMetric],
    queryFn: () => fetchBaseline(`custom.googleapis.com/${selectedService}/${selectedMetric}`, 7),
    refetchInterval: 3600000, // Refresh every hour
  });

  const formatChartData = (metricKey: string) => {
    if (!metricsData?.[metricKey]) return [];
    
    return metricsData[metricKey].map((point: any) => ({
      timestamp: new Date(point.timestamp).toLocaleTimeString(),
      value: point.value,
      baseline: baselineData?.mean || 0,
    }));
  };

  const calculateDeviation = (currentValue: number, baseline: number) => {
    if (!baseline) return 0;
    return ((currentValue - baseline) / baseline) * 100;
  };

  const getDeviationIcon = (deviation: number) => {
    if (Math.abs(deviation) < 5) return <Minus className="h-4 w-4 text-muted-foreground" />;
    if (deviation > 0) return <TrendingUp className="h-4 w-4 text-destructive" />;
    return <TrendingDown className="h-4 w-4 text-success" />;
  };

  if (metricsLoading || baselineLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <label className="text-sm font-medium mb-2 block">Service</label>
          <Select value={selectedService} onValueChange={setSelectedService}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SERVICES.map((service) => (
                <SelectItem key={service.value} value={service.value}>
                  {service.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex-1">
          <label className="text-sm font-medium mb-2 block">Time Range</label>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TIME_RANGES.map((range) => (
                <SelectItem key={range.value} value={range.value}>
                  {range.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Metric Cards with Baseline Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {METRICS.map((metric) => {
          const currentData = metricsData?.[metric.key];
          const currentValue = currentData?.[currentData.length - 1]?.value || 0;
          const deviation = calculateDeviation(currentValue, baselineData?.mean || 0);

          return (
            <Card
              key={metric.key}
              className={`cursor-pointer transition-colors ${
                selectedMetric === metric.key ? 'border-brand' : ''
              }`}
              onClick={() => setSelectedMetric(metric.key)}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">{metric.label}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline justify-between">
                  <div className="text-2xl font-semibold">
                    {currentValue.toFixed(1)}
                    <span className="text-sm text-muted-foreground ml-1">{metric.unit}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {getDeviationIcon(deviation)}
                    <span
                      className={`text-sm ${
                        Math.abs(deviation) < 5
                          ? 'text-muted-foreground'
                          : deviation > 0
                          ? 'text-destructive'
                          : 'text-success'
                      }`}
                    >
                      {deviation > 0 ? '+' : ''}
                      {deviation.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Baseline: {baselineData?.mean?.toFixed(1) || 0} {metric.unit}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Detailed Chart */}
      <Card>
        <CardHeader>
          <CardTitle>
            {METRICS.find((m) => m.key === selectedMetric)?.label} - Historical Trend
          </CardTitle>
          <CardDescription>
            Showing {timeRange} of data with 7-day baseline comparison
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={formatChartData(selectedMetric)}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="timestamp"
                  stroke="hsl(var(--muted-foreground))"
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                />
                <YAxis
                  stroke="hsl(var(--muted-foreground))"
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                  label={{
                    value: METRICS.find((m) => m.key === selectedMetric)?.unit || '',
                    angle: -90,
                    position: 'insideLeft',
                    style: { fill: 'hsl(var(--muted-foreground))' },
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                />
                <Legend />
                <ReferenceLine
                  y={baselineData?.mean || 0}
                  stroke="hsl(var(--muted-foreground))"
                  strokeDasharray="5 5"
                  label={{ value: 'Baseline', fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={METRICS.find((m) => m.key === selectedMetric)?.color}
                  strokeWidth={2}
                  dot={false}
                  name="Current"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Baseline Statistics */}
          {baselineData && (
            <div className="mt-6 grid grid-cols-2 md:grid-cols-5 gap-4 pt-4 border-t">
              <div>
                <p className="text-xs text-muted-foreground">Mean</p>
                <p className="text-sm font-medium">{baselineData.mean.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Median</p>
                <p className="text-sm font-medium">{baselineData.median.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Std Dev</p>
                <p className="text-sm font-medium">{baselineData.std_dev.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">P95</p>
                <p className="text-sm font-medium">{baselineData.p95.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">P99</p>
                <p className="text-sm font-medium">{baselineData.p99.toFixed(2)}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

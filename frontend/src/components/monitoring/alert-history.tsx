'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { fetchAlertHistory } from '@/lib/api';
import { AlertHistoryItem } from '@/types';
import { Clock, CheckCircle, AlertCircle, Filter } from 'lucide-react';
import { format, parseISO, differenceInMinutes } from 'date-fns';

const SEVERITY_COLORS = {
  info: 'hsl(var(--exchange))',
  warning: 'hsl(var(--mempool))',
  critical: 'hsl(var(--destructive))',
};

export function AlertHistory() {
  const { user, getIdToken } = useAuth();
  const [filters, setFilters] = useState({
    service: '',
    severity: '',
    start_date: '',
    end_date: '',
  });

  const { data: historyData, isLoading } = useQuery({
    queryKey: ['alert-history', filters],
    queryFn: async () => {
      const token = user ? await getIdToken() : undefined;
      return fetchAlertHistory(filters, token);
    },
    refetchInterval: 60000, // Refresh every minute
  });

  const calculateMTTR = (alerts: AlertHistoryItem[]) => {
    const resolvedAlerts = alerts.filter((a) => a.resolved_at);
    if (resolvedAlerts.length === 0) return 0;

    const totalMinutes = resolvedAlerts.reduce((sum, alert) => {
      const triggered = parseISO(alert.triggered_at);
      const resolved = parseISO(alert.resolved_at!);
      return sum + differenceInMinutes(resolved, triggered);
    }, 0);

    return totalMinutes / resolvedAlerts.length;
  };

  const getAlertFrequencyData = (alerts: AlertHistoryItem[]) => {
    const serviceCount: Record<string, number> = {};
    alerts.forEach((alert) => {
      const service = alert.message.split(':')[0] || 'Unknown';
      serviceCount[service] = (serviceCount[service] || 0) + 1;
    });

    return Object.entries(serviceCount).map(([name, count]) => ({
      name,
      count,
    }));
  };

  const getSeverityDistribution = (alerts: AlertHistoryItem[]) => {
    const severityCount: Record<string, number> = {
      info: 0,
      warning: 0,
      critical: 0,
    };

    alerts.forEach((alert) => {
      severityCount[alert.severity] = (severityCount[alert.severity] || 0) + 1;
    });

    return Object.entries(severityCount).map(([name, value]) => ({
      name,
      value,
    }));
  };

  const alerts = historyData?.alerts || [];
  const mttr = calculateMTTR(alerts);
  const frequencyData = getAlertFrequencyData(alerts);
  const severityData = getSeverityDistribution(alerts);

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="service-filter">Service</Label>
              <Select
                value={filters.service}
                onValueChange={(value) => setFilters({ ...filters, service: value })}
              >
                <SelectTrigger id="service-filter">
                  <SelectValue placeholder="All services" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All services</SelectItem>
                  <SelectItem value="web-api">Web API</SelectItem>
                  <SelectItem value="feature-engine">Feature Engine</SelectItem>
                  <SelectItem value="insight-generator">Insight Generator</SelectItem>
                  <SelectItem value="chart-renderer">Chart Renderer</SelectItem>
                  <SelectItem value="data-ingestion">Data Ingestion</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="severity-filter">Severity</Label>
              <Select
                value={filters.severity}
                onValueChange={(value) => setFilters({ ...filters, severity: value })}
              >
                <SelectTrigger id="severity-filter">
                  <SelectValue placeholder="All severities" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All severities</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="warning">Warning</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="start-date">Start Date</Label>
              <Input
                id="start-date"
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="end-date">End Date</Label>
              <Input
                id="end-date"
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{alerts.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {alerts.filter((a) => !a.resolved_at).length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Mean Time to Resolution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{mttr.toFixed(1)}</div>
            <p className="text-xs text-muted-foreground mt-1">minutes</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Resolution Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">
              {alerts.length > 0
                ? ((alerts.filter((a) => a.resolved_at).length / alerts.length) * 100).toFixed(1)
                : 0}
              %
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {alerts.filter((a) => a.resolved_at).length} of {alerts.length} resolved
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Alert Frequency by Service</CardTitle>
            <CardDescription>Number of alerts triggered per service</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={frequencyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                  <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                  <Bar dataKey="count" fill="hsl(var(--brand))" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Severity Distribution</CardTitle>
            <CardDescription>Breakdown of alerts by severity level</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="hsl(var(--primary))"
                    dataKey="value"
                  >
                    {severityData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={SEVERITY_COLORS[entry.name as keyof typeof SEVERITY_COLORS]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alert History Table */}
      <Card>
        <CardHeader>
          <CardTitle>Alert History</CardTitle>
          <CardDescription>Recent alert triggers and resolutions</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-center text-muted-foreground py-8">Loading alert history...</p>
          ) : alerts.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No alerts found</p>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert: AlertHistoryItem) => (
                <div key={alert.id} className="flex items-start gap-4 p-4 border rounded-lg">
                  <div className="flex-shrink-0 mt-1">
                    {alert.resolved_at ? (
                      <CheckCircle className="h-5 w-5 text-success" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-destructive" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge
                        variant="outline"
                        className={
                          alert.severity === 'critical'
                            ? 'bg-red-500'
                            : alert.severity === 'warning'
                            ? 'bg-yellow-500'
                            : 'bg-blue-500'
                        }
                      >
                        {alert.severity}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        {format(parseISO(alert.triggered_at), 'MMM dd, yyyy HH:mm')}
                      </span>
                    </div>
                    <p className="text-sm font-medium mb-1">{alert.message}</p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>
                        Value: {alert.metric_value.toFixed(2)} (Threshold:{' '}
                        {alert.threshold_value.toFixed(2)})
                      </span>
                      {alert.resolved_at && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Resolved in{' '}
                          {differenceInMinutes(
                            parseISO(alert.resolved_at),
                            parseISO(alert.triggered_at)
                          )}{' '}
                          min
                        </span>
                      )}
                    </div>
                  </div>
                  {!alert.resolved_at && (
                    <Button variant="outline" size="sm">
                      Resolve
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

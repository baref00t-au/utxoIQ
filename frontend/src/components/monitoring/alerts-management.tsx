'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  fetchAlertConfigurations,
  createAlertConfiguration,
  updateAlertConfiguration,
  deleteAlertConfiguration,
} from '@/lib/api';
import { AlertConfiguration } from '@/types';
import { Plus, Trash2, Bell, BellOff, Mail, MessageSquare, Smartphone } from 'lucide-react';
import { toast } from 'sonner';

const SERVICES = [
  'web-api',
  'feature-engine',
  'insight-generator',
  'chart-renderer',
  'data-ingestion',
];

const METRICS = [
  { value: 'cpu_usage', label: 'CPU Usage' },
  { value: 'memory_usage', label: 'Memory Usage' },
  { value: 'response_time', label: 'Response Time' },
  { value: 'error_rate', label: 'Error Rate' },
  { value: 'request_count', label: 'Request Count' },
];

const THRESHOLD_TYPES = [
  { value: 'absolute', label: 'Absolute Value' },
  { value: 'percentage', label: 'Percentage Change' },
  { value: 'rate', label: 'Rate of Change' },
];

const OPERATORS = [
  { value: '>', label: 'Greater Than (>)' },
  { value: '<', label: 'Less Than (<)' },
  { value: '>=', label: 'Greater or Equal (>=)' },
  { value: '<=', label: 'Less or Equal (<=)' },
  { value: '==', label: 'Equal To (==)' },
];

const SEVERITIES = [
  { value: 'info', label: 'Info', color: 'bg-blue-500' },
  { value: 'warning', label: 'Warning', color: 'bg-yellow-500' },
  { value: 'critical', label: 'Critical', color: 'bg-red-500' },
];

export function AlertsManagement() {
  const { user, getIdToken } = useAuth();
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    service_name: '',
    metric_type: '',
    threshold_type: 'absolute' as const,
    threshold_value: '',
    comparison_operator: '>' as const,
    severity: 'warning' as const,
    evaluation_window_seconds: '300',
    notification_channels: [] as string[],
  });

  const { data: alerts, isLoading } = useQuery({
    queryKey: ['alert-configurations'],
    queryFn: async () => {
      const token = await getIdToken();
      return fetchAlertConfigurations(token);
    },
    enabled: !!user,
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const token = await getIdToken();
      return createAlertConfiguration(data, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-configurations'] });
      toast.success('Alert configuration created successfully');
      resetForm();
      setIsCreating(false);
    },
    onError: () => {
      toast.error('Failed to create alert configuration');
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const token = await getIdToken();
      return updateAlertConfiguration(id, data, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-configurations'] });
      toast.success('Alert configuration updated');
    },
    onError: () => {
      toast.error('Failed to update alert configuration');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getIdToken();
      return deleteAlertConfiguration(id, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-configurations'] });
      toast.success('Alert configuration deleted');
    },
    onError: () => {
      toast.error('Failed to delete alert configuration');
    },
  });

  const resetForm = () => {
    setFormData({
      name: '',
      service_name: '',
      metric_type: '',
      threshold_type: 'absolute',
      threshold_value: '',
      comparison_operator: '>',
      severity: 'warning',
      evaluation_window_seconds: '300',
      notification_channels: [],
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.service_name || !formData.metric_type || !formData.threshold_value) {
      toast.error('Please fill in all required fields');
      return;
    }

    createMutation.mutate({
      ...formData,
      threshold_value: parseFloat(formData.threshold_value),
      evaluation_window_seconds: parseInt(formData.evaluation_window_seconds),
    });
  };

  const toggleChannel = (channel: string) => {
    setFormData((prev) => ({
      ...prev,
      notification_channels: prev.notification_channels.includes(channel)
        ? prev.notification_channels.filter((c) => c !== channel)
        : [...prev.notification_channels, channel],
    }));
  };

  const toggleAlertEnabled = (alert: AlertConfiguration) => {
    updateMutation.mutate({
      id: alert.id,
      data: { enabled: !alert.enabled },
    });
  };

  if (!user) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">
            Please sign in to manage alert configurations
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Alert Creation Form */}
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Create Alert
          </CardTitle>
          <CardDescription>Configure a new alert threshold</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Alert Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="High CPU Usage"
              />
            </div>

            <div>
              <Label htmlFor="service">Service *</Label>
              <Select
                value={formData.service_name}
                onValueChange={(value) => setFormData({ ...formData, service_name: value })}
              >
                <SelectTrigger id="service">
                  <SelectValue placeholder="Select service" />
                </SelectTrigger>
                <SelectContent>
                  {SERVICES.map((service) => (
                    <SelectItem key={service} value={service}>
                      {service}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="metric">Metric *</Label>
              <Select
                value={formData.metric_type}
                onValueChange={(value) => setFormData({ ...formData, metric_type: value })}
              >
                <SelectTrigger id="metric">
                  <SelectValue placeholder="Select metric" />
                </SelectTrigger>
                <SelectContent>
                  {METRICS.map((metric) => (
                    <SelectItem key={metric.value} value={metric.value}>
                      {metric.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label htmlFor="threshold-type">Threshold Type</Label>
                <Select
                  value={formData.threshold_type}
                  onValueChange={(value: any) =>
                    setFormData({ ...formData, threshold_type: value })
                  }
                >
                  <SelectTrigger id="threshold-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {THRESHOLD_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="operator">Operator</Label>
                <Select
                  value={formData.comparison_operator}
                  onValueChange={(value: any) =>
                    setFormData({ ...formData, comparison_operator: value })
                  }
                >
                  <SelectTrigger id="operator">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {OPERATORS.map((op) => (
                      <SelectItem key={op.value} value={op.value}>
                        {op.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="threshold">Threshold Value *</Label>
              <Input
                id="threshold"
                type="number"
                step="0.01"
                value={formData.threshold_value}
                onChange={(e) => setFormData({ ...formData, threshold_value: e.target.value })}
                placeholder="80"
              />
            </div>

            <div>
              <Label htmlFor="severity">Severity</Label>
              <Select
                value={formData.severity}
                onValueChange={(value: any) => setFormData({ ...formData, severity: value })}
              >
                <SelectTrigger id="severity">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SEVERITIES.map((sev) => (
                    <SelectItem key={sev.value} value={sev.value}>
                      {sev.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="window">Evaluation Window (seconds)</Label>
              <Input
                id="window"
                type="number"
                value={formData.evaluation_window_seconds}
                onChange={(e) =>
                  setFormData({ ...formData, evaluation_window_seconds: e.target.value })
                }
              />
            </div>

            <div>
              <Label className="mb-3 block">Notification Channels</Label>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    <span className="text-sm">Email</span>
                  </div>
                  <Switch
                    checked={formData.notification_channels.includes('email')}
                    onCheckedChange={() => toggleChannel('email')}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    <span className="text-sm">Slack</span>
                  </div>
                  <Switch
                    checked={formData.notification_channels.includes('slack')}
                    onCheckedChange={() => toggleChannel('slack')}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Smartphone className="h-4 w-4" />
                    <span className="text-sm">SMS (Critical only)</span>
                  </div>
                  <Switch
                    checked={formData.notification_channels.includes('sms')}
                    onCheckedChange={() => toggleChannel('sms')}
                    disabled={formData.severity !== 'critical'}
                  />
                </div>
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Alert'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Alert List */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Configured Alerts</CardTitle>
          <CardDescription>Manage your alert configurations</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-center text-muted-foreground py-8">Loading alerts...</p>
          ) : !alerts || alerts.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No alerts configured. Create your first alert to get started.
            </p>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert: AlertConfiguration) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium">{alert.name}</h4>
                      <Badge
                        variant="outline"
                        className={
                          SEVERITIES.find((s) => s.value === alert.severity)?.color || ''
                        }
                      >
                        {alert.severity}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {alert.service_name} • {alert.metric_type} {alert.comparison_operator}{' '}
                      {alert.threshold_value}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      {alert.notification_channels.map((channel) => (
                        <Badge key={channel} variant="secondary" className="text-xs">
                          {channel}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => toggleAlertEnabled(alert)}
                      disabled={updateMutation.isPending}
                    >
                      {alert.enabled ? (
                        <Bell className="h-4 w-4 text-success" />
                      ) : (
                        <BellOff className="h-4 w-4 text-muted-foreground" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteMutation.mutate(alert.id)}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

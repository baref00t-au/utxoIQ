'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import {
  fetchDashboards,
  createDashboard,
  updateDashboard,
  fetchWidgetData,
} from '@/lib/api';
import { DashboardConfiguration, DashboardWidget } from '@/types';
import {
  Plus,
  LayoutDashboard,
  Trash2,
  Share2,
  Copy,
  LineChart,
  BarChart3,
  Gauge,
  Activity,
} from 'lucide-react';
import { toast } from 'sonner';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const WIDGET_TYPES = [
  { value: 'line_chart', label: 'Line Chart', icon: LineChart },
  { value: 'bar_chart', label: 'Bar Chart', icon: BarChart3 },
  { value: 'gauge', label: 'Gauge', icon: Gauge },
  { value: 'stat_card', label: 'Stat Card', icon: Activity },
];

const METRICS = [
  'cpu_usage',
  'memory_usage',
  'response_time',
  'error_rate',
  'request_count',
];

const TIME_RANGES = ['1h', '4h', '24h', '7d', '30d'];

export function CustomDashboards() {
  const { user, getIdToken } = useAuth();
  const queryClient = useQueryClient();
  const [selectedDashboard, setSelectedDashboard] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newDashboardName, setNewDashboardName] = useState('');
  const [isAddingWidget, setIsAddingWidget] = useState(false);
  const [newWidget, setNewWidget] = useState({
    type: 'line_chart',
    title: '',
    metric_type: '',
    aggregation: 'ALIGN_MEAN',
    time_range: '24h',
  });

  const { data: dashboards, isLoading } = useQuery({
    queryKey: ['dashboards'],
    queryFn: async () => {
      const token = await getIdToken();
      return fetchDashboards(token);
    },
    enabled: !!user,
  });

  const createMutation = useMutation({
    mutationFn: async (name: string) => {
      const token = await getIdToken();
      return createDashboard(
        {
          name,
          widgets: [],
          is_public: false,
        },
        token
      );
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      toast.success('Dashboard created successfully');
      setSelectedDashboard(data.id);
      setIsCreating(false);
      setNewDashboardName('');
    },
    onError: () => {
      toast.error('Failed to create dashboard');
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const token = await getIdToken();
      return updateDashboard(id, data, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      toast.success('Dashboard updated');
    },
    onError: () => {
      toast.error('Failed to update dashboard');
    },
  });

  const handleCreateDashboard = () => {
    if (!newDashboardName.trim()) {
      toast.error('Please enter a dashboard name');
      return;
    }
    createMutation.mutate(newDashboardName);
  };

  const handleAddWidget = () => {
    if (!selectedDashboard || !newWidget.title || !newWidget.metric_type) {
      toast.error('Please fill in all widget fields');
      return;
    }

    const dashboard = dashboards?.find((d: DashboardConfiguration) => d.id === selectedDashboard);
    if (!dashboard) return;

    const widget: DashboardWidget = {
      id: `widget-${Date.now()}`,
      type: newWidget.type as any,
      title: newWidget.title,
      data_source: {
        metric_type: newWidget.metric_type,
        aggregation: newWidget.aggregation,
        time_range: newWidget.time_range,
      },
      display_options: {},
      position: {
        x: 0,
        y: dashboard.widgets.length * 2,
        w: 6,
        h: 2,
      },
    };

    updateMutation.mutate({
      id: selectedDashboard,
      data: {
        widgets: [...dashboard.widgets, widget],
      },
    });

    setIsAddingWidget(false);
    setNewWidget({
      type: 'line_chart',
      title: '',
      metric_type: '',
      aggregation: 'ALIGN_MEAN',
      time_range: '24h',
    });
  };

  const handleRemoveWidget = (widgetId: string) => {
    if (!selectedDashboard) return;

    const dashboard = dashboards?.find((d: DashboardConfiguration) => d.id === selectedDashboard);
    if (!dashboard) return;

    updateMutation.mutate({
      id: selectedDashboard,
      data: {
        widgets: dashboard.widgets.filter((w: DashboardWidget) => w.id !== widgetId),
      },
    });
  };

  const handleShareDashboard = (dashboardId: string) => {
    const dashboard = dashboards?.find((d: DashboardConfiguration) => d.id === dashboardId);
    if (!dashboard) return;

    updateMutation.mutate({
      id: dashboardId,
      data: {
        is_public: !dashboard.is_public,
      },
    });
  };

  const currentDashboard = dashboards?.find(
    (d: DashboardConfiguration) => d.id === selectedDashboard
  );

  if (!user) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">
            Please sign in to create custom dashboards
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Selector */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <Select value={selectedDashboard || ''} onValueChange={setSelectedDashboard}>
            <SelectTrigger>
              <SelectValue placeholder="Select a dashboard" />
            </SelectTrigger>
            <SelectContent>
              {dashboards?.map((dashboard: DashboardConfiguration) => (
                <SelectItem key={dashboard.id} value={dashboard.id}>
                  {dashboard.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Dialog open={isCreating} onOpenChange={setIsCreating}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Dashboard
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Dashboard</DialogTitle>
              <DialogDescription>
                Create a new custom monitoring dashboard
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="dashboard-name">Dashboard Name</Label>
                <Input
                  id="dashboard-name"
                  value={newDashboardName}
                  onChange={(e) => setNewDashboardName(e.target.value)}
                  placeholder="My Dashboard"
                />
              </div>
              <Button onClick={handleCreateDashboard} disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating...' : 'Create Dashboard'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Dashboard Content */}
      {currentDashboard ? (
        <>
          {/* Dashboard Header */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <LayoutDashboard className="h-5 w-5" />
                    {currentDashboard.name}
                  </CardTitle>
                  <CardDescription>
                    {currentDashboard.widgets.length} widgets •{' '}
                    {currentDashboard.is_public ? 'Public' : 'Private'}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleShareDashboard(currentDashboard.id)}
                  >
                    <Share2 className="h-4 w-4 mr-2" />
                    {currentDashboard.is_public ? 'Make Private' : 'Share'}
                  </Button>
                  {currentDashboard.is_public && currentDashboard.share_token && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        navigator.clipboard.writeText(
                          `${window.location.origin}/monitoring/dashboard/${currentDashboard.share_token}`
                        );
                        toast.success('Share link copied to clipboard');
                      }}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Widgets */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {currentDashboard.widgets.map((widget: DashboardWidget) => (
              <WidgetCard
                key={widget.id}
                widget={widget}
                dashboardId={currentDashboard.id}
                onRemove={() => handleRemoveWidget(widget.id)}
              />
            ))}

            {/* Add Widget Card */}
            <Card className="border-dashed">
              <CardContent className="flex items-center justify-center h-full min-h-[200px]">
                <Dialog open={isAddingWidget} onOpenChange={setIsAddingWidget}>
                  <DialogTrigger asChild>
                    <Button variant="outline">
                      <Plus className="h-4 w-4 mr-2" />
                      Add Widget
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Widget</DialogTitle>
                      <DialogDescription>Configure a new dashboard widget</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="widget-type">Widget Type</Label>
                        <Select
                          value={newWidget.type}
                          onValueChange={(value) => setNewWidget({ ...newWidget, type: value })}
                        >
                          <SelectTrigger id="widget-type">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {WIDGET_TYPES.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label htmlFor="widget-title">Title</Label>
                        <Input
                          id="widget-title"
                          value={newWidget.title}
                          onChange={(e) => setNewWidget({ ...newWidget, title: e.target.value })}
                          placeholder="CPU Usage"
                        />
                      </div>

                      <div>
                        <Label htmlFor="widget-metric">Metric</Label>
                        <Select
                          value={newWidget.metric_type}
                          onValueChange={(value) =>
                            setNewWidget({ ...newWidget, metric_type: value })
                          }
                        >
                          <SelectTrigger id="widget-metric">
                            <SelectValue placeholder="Select metric" />
                          </SelectTrigger>
                          <SelectContent>
                            {METRICS.map((metric) => (
                              <SelectItem key={metric} value={metric}>
                                {metric}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label htmlFor="widget-time-range">Time Range</Label>
                        <Select
                          value={newWidget.time_range}
                          onValueChange={(value) =>
                            setNewWidget({ ...newWidget, time_range: value })
                          }
                        >
                          <SelectTrigger id="widget-time-range">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {TIME_RANGES.map((range) => (
                              <SelectItem key={range} value={range}>
                                {range}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <Button onClick={handleAddWidget} disabled={updateMutation.isPending}>
                        {updateMutation.isPending ? 'Adding...' : 'Add Widget'}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </CardContent>
            </Card>
          </div>
        </>
      ) : (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <LayoutDashboard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-4">
                {dashboards?.length === 0
                  ? 'No dashboards yet. Create your first dashboard to get started.'
                  : 'Select a dashboard from the dropdown above'}
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function WidgetCard({
  widget,
  dashboardId,
  onRemove,
}: {
  widget: DashboardWidget;
  dashboardId: string;
  onRemove: () => void;
}) {
  const { getIdToken } = useAuth();

  const { data: widgetData } = useQuery({
    queryKey: ['widget-data', dashboardId, widget.id],
    queryFn: async () => {
      const token = await getIdToken();
      return fetchWidgetData(dashboardId, widget.id, token);
    },
    refetchInterval: 60000,
  });

  const renderWidget = () => {
    if (!widgetData) {
      return <div className="h-[200px] flex items-center justify-center">Loading...</div>;
    }

    switch (widget.type) {
      case 'line_chart':
        return (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={widgetData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="timestamp" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                }}
              />
              <Line type="monotone" dataKey="value" stroke="hsl(var(--brand))" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'bar_chart':
        return (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={widgetData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="timestamp" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                }}
              />
              <Bar dataKey="value" fill="hsl(var(--brand))" />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'stat_card':
        const value = widgetData[widgetData.length - 1]?.value || 0;
        return (
          <div className="h-[200px] flex flex-col items-center justify-center">
            <div className="text-4xl font-semibold">{value.toFixed(1)}</div>
            <p className="text-sm text-muted-foreground mt-2">Current Value</p>
          </div>
        );

      default:
        return <div className="h-[200px] flex items-center justify-center">Unsupported widget type</div>;
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{widget.title}</CardTitle>
          <Button variant="ghost" size="icon" onClick={onRemove}>
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
        <CardDescription className="text-xs">
          {widget.data_source.metric_type} • {widget.data_source.time_range}
        </CardDescription>
      </CardHeader>
      <CardContent>{renderWidget()}</CardContent>
    </Card>
  );
}

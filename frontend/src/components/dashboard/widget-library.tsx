'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, BarChart3, LineChart as LineChartIcon, Gauge, Activity } from 'lucide-react';
import { DashboardWidget } from '@/types';

interface WidgetTemplate {
  type: DashboardWidget['type'];
  title: string;
  description: string;
  icon: React.ReactNode;
  defaultSize: { w: number; h: number };
  defaultConfig: {
    metric_type: string;
    aggregation: string;
    time_range: string;
  };
}

const WIDGET_TEMPLATES: WidgetTemplate[] = [
  {
    type: 'line_chart',
    title: 'Line Chart',
    description: 'Display time-series data with a line chart',
    icon: <LineChartIcon className="h-6 w-6" />,
    defaultSize: { w: 6, h: 2 },
    defaultConfig: {
      metric_type: 'cpu_usage',
      aggregation: 'avg',
      time_range: '24h',
    },
  },
  {
    type: 'bar_chart',
    title: 'Bar Chart',
    description: 'Compare values across categories',
    icon: <BarChart3 className="h-6 w-6" />,
    defaultSize: { w: 6, h: 2 },
    defaultConfig: {
      metric_type: 'request_count',
      aggregation: 'sum',
      time_range: '7d',
    },
  },
  {
    type: 'gauge',
    title: 'Gauge',
    description: 'Show a single metric as a percentage',
    icon: <Gauge className="h-6 w-6" />,
    defaultSize: { w: 3, h: 2 },
    defaultConfig: {
      metric_type: 'memory_usage',
      aggregation: 'current',
      time_range: 'now',
    },
  },
  {
    type: 'stat_card',
    title: 'Stat Card',
    description: 'Display a key metric with trend',
    icon: <Activity className="h-6 w-6" />,
    defaultSize: { w: 3, h: 1 },
    defaultConfig: {
      metric_type: 'active_users',
      aggregation: 'count',
      time_range: '24h',
    },
  },
];

interface WidgetLibraryProps {
  onAddWidget: (widget: Omit<DashboardWidget, 'id'>) => void;
}

export function WidgetLibrary({ onAddWidget }: WidgetLibraryProps) {
  const [open, setOpen] = useState(false);

  const handleAddWidget = (template: WidgetTemplate) => {
    const newWidget: Omit<DashboardWidget, 'id'> = {
      type: template.type,
      title: template.title,
      data_source: template.defaultConfig,
      display_options: {},
      position: {
        x: 0,
        y: 0,
        ...template.defaultSize,
      },
    };

    onAddWidget(newWidget);
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Add Widget
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Widget Library</DialogTitle>
          <DialogDescription>
            Choose a widget type to add to your dashboard
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4 py-4">
          {WIDGET_TEMPLATES.map((template) => (
            <Card
              key={template.type}
              className="cursor-pointer hover:border-brand transition-colors"
              onClick={() => handleAddWidget(template)}
            >
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-surface">
                    {template.icon}
                  </div>
                  <div>
                    <CardTitle className="text-base">{template.title}</CardTitle>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>{template.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}

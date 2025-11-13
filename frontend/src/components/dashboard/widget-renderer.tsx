'use client';

import { DashboardWidget } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, TrendingUp, AlertCircle } from 'lucide-react';

interface WidgetRendererProps {
  widget: DashboardWidget;
}

export function WidgetRenderer({ widget }: WidgetRendererProps) {
  switch (widget.type) {
    case 'line_chart':
      return <LineChartWidget widget={widget} />;
    case 'bar_chart':
      return <BarChartWidget widget={widget} />;
    case 'gauge':
      return <GaugeWidget widget={widget} />;
    case 'stat_card':
      return <StatCardWidget widget={widget} />;
    default:
      return <DefaultWidget widget={widget} />;
  }
}

function LineChartWidget({ widget }: WidgetRendererProps) {
  // Mock data for demonstration
  const data = Array.from({ length: 24 }, (_, i) => ({
    time: `${i}:00`,
    value: Math.floor(Math.random() * 100) + 50,
  }));

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base">{widget.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <XAxis dataKey="time" fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="value"
              stroke="hsl(var(--brand))"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function BarChartWidget({ widget }: WidgetRendererProps) {
  // Mock data for demonstration
  const data = Array.from({ length: 7 }, (_, i) => ({
    day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i],
    value: Math.floor(Math.random() * 100) + 20,
  }));

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base">{widget.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data}>
            <XAxis dataKey="day" fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip />
            <Bar dataKey="value" fill="hsl(var(--brand))" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function GaugeWidget({ widget }: WidgetRendererProps) {
  // Mock value for demonstration
  const value = Math.floor(Math.random() * 100);
  const percentage = value;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base">{widget.title}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-center">
        <div className="relative w-32 h-32">
          <svg className="w-full h-full" viewBox="0 0 100 100">
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="hsl(var(--border))"
              strokeWidth="8"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="hsl(var(--brand))"
              strokeWidth="8"
              strokeDasharray={`${(percentage / 100) * 251.2} 251.2`}
              strokeLinecap="round"
              transform="rotate(-90 50 50)"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold">{value}%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function StatCardWidget({ widget }: WidgetRendererProps) {
  // Mock data for demonstration
  const value = Math.floor(Math.random() * 10000);
  const change = (Math.random() * 20 - 10).toFixed(1);
  const isPositive = parseFloat(change) > 0;

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{widget.title}</CardTitle>
        <Activity className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value.toLocaleString()}</div>
        <p className={`text-xs ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
          {isPositive ? '+' : ''}{change}% from last period
        </p>
      </CardContent>
    </Card>
  );
}

function DefaultWidget({ widget }: WidgetRendererProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base">{widget.title}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-center h-32">
        <div className="text-center text-muted-foreground">
          <AlertCircle className="h-8 w-8 mx-auto mb-2" />
          <p className="text-sm">Widget type not supported</p>
        </div>
      </CardContent>
    </Card>
  );
}

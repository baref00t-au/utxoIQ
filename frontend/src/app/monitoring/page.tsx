'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MetricsDashboard } from '@/components/monitoring/metrics-dashboard';
import { AlertsManagement } from '@/components/monitoring/alerts-management';
import { AlertHistory } from '@/components/monitoring/alert-history';
import { DependencyVisualization } from '@/components/monitoring/dependency-visualization';
import { LogSearch } from '@/components/monitoring/log-search';
import { TraceViewer } from '@/components/monitoring/trace-viewer';
import { CustomDashboards } from '@/components/monitoring/custom-dashboards';
import {
  Activity,
  Bell,
  History,
  Network,
  FileText,
  GitBranch,
  LayoutDashboard,
} from 'lucide-react';

export default function MonitoringPage() {
  const [activeTab, setActiveTab] = useState('metrics');

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold mb-2">System Monitoring</h1>
        <p className="text-muted-foreground">
          Monitor system performance, configure alerts, and analyze service dependencies
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-7 lg:w-auto">
          <TabsTrigger value="metrics" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            <span className="hidden sm:inline">Metrics</span>
          </TabsTrigger>
          <TabsTrigger value="alerts" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            <span className="hidden sm:inline">Alerts</span>
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            <span className="hidden sm:inline">History</span>
          </TabsTrigger>
          <TabsTrigger value="dependencies" className="flex items-center gap-2">
            <Network className="h-4 w-4" />
            <span className="hidden sm:inline">Dependencies</span>
          </TabsTrigger>
          <TabsTrigger value="logs" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            <span className="hidden sm:inline">Logs</span>
          </TabsTrigger>
          <TabsTrigger value="traces" className="flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            <span className="hidden sm:inline">Traces</span>
          </TabsTrigger>
          <TabsTrigger value="dashboards" className="flex items-center gap-2">
            <LayoutDashboard className="h-4 w-4" />
            <span className="hidden sm:inline">Dashboards</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="metrics" className="space-y-4">
          <MetricsDashboard />
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <AlertsManagement />
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <AlertHistory />
        </TabsContent>

        <TabsContent value="dependencies" className="space-y-4">
          <DependencyVisualization />
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <LogSearch />
        </TabsContent>

        <TabsContent value="traces" className="space-y-4">
          <TraceViewer />
        </TabsContent>

        <TabsContent value="dashboards" className="space-y-4">
          <CustomDashboards />
        </TabsContent>
      </Tabs>
    </div>
  );
}

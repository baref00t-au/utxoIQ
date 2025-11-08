import { Metadata } from 'next';
import { SystemStatusDashboard } from '@/components/dashboard/system-status';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { InsightFeed } from '@/components/insights/insight-feed';

export const metadata: Metadata = {
  title: 'Dashboard | utxoIQ',
  description: 'Real-time Bitcoin blockchain intelligence dashboard',
};

export default function DashboardPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-semibold">Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor system health, insights, and blockchain intelligence
          </p>
        </div>

        <Tabs defaultValue="insights" className="space-y-6">
          <TabsList>
            <TabsTrigger value="insights">Insights</TabsTrigger>
            <TabsTrigger value="system">System Status</TabsTrigger>
            <TabsTrigger value="metrics">Metrics</TabsTrigger>
          </TabsList>

          <TabsContent value="insights" className="space-y-4">
            <InsightFeed />
          </TabsContent>

          <TabsContent value="system" className="space-y-4">
            <SystemStatusDashboard />
          </TabsContent>

          <TabsContent value="metrics" className="space-y-4">
            <MetricsView />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function MetricsView() {
  return (
    <div className="grid gap-6">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="font-semibold">Signal Generation (24h)</h3>
          <p className="text-sm text-muted-foreground">
            Metrics will be available when the API is running
          </p>
        </div>
        <div className="rounded-lg border p-6 space-y-4">
          <h3 className="font-semibold">Insight Generation (24h)</h3>
          <p className="text-sm text-muted-foreground">
            Metrics will be available when the API is running
          </p>
        </div>
      </div>
    </div>
  );
}

'use client';

import { useDashboardPersistence } from '@/hooks/use-dashboard-persistence';
import { DashboardLayout } from './dashboard-layout';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, AlertCircle, Save } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface CustomizableDashboardProps {
  dashboardId?: string;
  userId?: string;
  editable?: boolean;
}

export function CustomizableDashboard({
  dashboardId,
  userId,
  editable = true,
}: CustomizableDashboardProps) {
  const {
    widgets,
    isLoading,
    isSaving,
    error,
    addWidget,
    removeWidget,
    updateWidgets,
    saveDashboard,
  } = useDashboardPersistence({
    dashboardId,
    userId,
    enabled: !!dashboardId,
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading dashboard...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <div className="ml-3">
            <p className="font-medium text-destructive">Failed to load dashboard</p>
            <p className="text-sm text-muted-foreground">{error.message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Status indicator */}
      {editable && (
        <div className="flex justify-end">
          {isSaving && (
            <Badge variant="secondary" className="gap-2">
              <Save className="h-3 w-3 animate-pulse" />
              Saving...
            </Badge>
          )}
        </div>
      )}

      {/* Dashboard layout */}
      <DashboardLayout
        widgets={widgets}
        onLayoutChange={updateWidgets}
        onAddWidget={addWidget}
        onRemoveWidget={removeWidget}
        editable={editable}
        showControls={editable}
      />

      {/* Empty state */}
      {widgets.length === 0 && editable && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <p className="text-lg font-medium mb-2">Your dashboard is empty</p>
            <p className="text-sm text-muted-foreground mb-4">
              Click "Add Widget" to start customizing your dashboard
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

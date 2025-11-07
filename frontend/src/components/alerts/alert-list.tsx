'use client';

import { Alert } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Loader2, Trash2, Bell, BellOff } from 'lucide-react';
import { formatDate } from '@/lib/utils';

interface AlertListProps {
  alerts: Alert[];
  isLoading: boolean;
  onToggle: (alertId: string, isActive: boolean) => void;
  onDelete: (alertId: string) => void;
}

const categoryLabels = {
  mempool: 'Mempool Fees',
  exchange: 'Exchange Flows',
  miner: 'Miner Treasury',
  whale: 'Whale Activity',
};

const operatorLabels = {
  gt: '>',
  lt: '<',
  eq: '=',
};

export function AlertList({ alerts, isLoading, onToggle, onDelete }: AlertListProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-brand" />
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="rounded-2xl border border-border bg-card p-12 text-center">
        <BellOff className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h3 className="text-lg font-semibold mb-2">No alerts yet</h3>
        <p className="text-sm text-muted-foreground">
          Create your first alert to get notified about blockchain events
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Your Alerts ({alerts.length})</h2>
      </div>
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className="rounded-2xl border border-border bg-card p-6 flex items-center justify-between"
        >
          <div className="flex items-center gap-4 flex-1">
            <div className={alert.is_active ? 'text-brand' : 'text-muted-foreground'}>
              {alert.is_active ? (
                <Bell className="w-5 h-5" />
              ) : (
                <BellOff className="w-5 h-5" />
              )}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="secondary">{categoryLabels[alert.signal_type]}</Badge>
                <span className="text-sm text-muted-foreground">
                  {operatorLabels[alert.operator]} {alert.threshold}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Created {formatDate(alert.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Switch
              checked={alert.is_active}
              onCheckedChange={(checked) => onToggle(alert.id, checked)}
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(alert.id)}
            >
              <Trash2 className="w-4 h-4 text-destructive" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

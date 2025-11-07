'use client';

import { useState } from 'react';
import { Alert, SignalType } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2 } from 'lucide-react';

interface AlertFormProps {
  onSubmit: (alert: Partial<Alert>) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function AlertForm({ onSubmit, onCancel, isLoading }: AlertFormProps) {
  const [signalType, setSignalType] = useState<SignalType>('mempool');
  const [threshold, setThreshold] = useState('');
  const [operator, setOperator] = useState<'gt' | 'lt' | 'eq'>('gt');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      signal_type: signalType,
      threshold: parseFloat(threshold),
      operator,
      is_active: true,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <h2 className="text-xl font-semibold">Create Alert</h2>

      <div className="space-y-2">
        <Label htmlFor="signal-type">Metric</Label>
        <Select value={signalType} onValueChange={(value) => setSignalType(value as SignalType)}>
          <SelectTrigger id="signal-type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="mempool">Mempool Fees</SelectItem>
            <SelectItem value="exchange">Exchange Flows</SelectItem>
            <SelectItem value="miner">Miner Treasury</SelectItem>
            <SelectItem value="whale">Whale Activity</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="operator">Condition</Label>
        <Select value={operator} onValueChange={(value) => setOperator(value as 'gt' | 'lt' | 'eq')}>
          <SelectTrigger id="operator">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="gt">Greater than</SelectItem>
            <SelectItem value="lt">Less than</SelectItem>
            <SelectItem value="eq">Equal to</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="threshold">Threshold</Label>
        <Input
          id="threshold"
          type="number"
          step="0.01"
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
          placeholder="Enter threshold value"
          required
        />
        <p className="text-xs text-muted-foreground">
          You'll be notified when this condition is met
        </p>
      </div>

      <div className="flex gap-2 pt-4">
        <Button type="submit" disabled={isLoading} className="flex-1">
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Creating...
            </>
          ) : (
            'Create Alert'
          )}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { Alert } from '@/types';
import { Button } from '@/components/ui/button';
import { AlertForm } from './alert-form';
import { AlertList } from './alert-list';
import { Bell, Plus } from 'lucide-react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAlerts(userId: string, token: string): Promise<Alert[]> {
  const response = await fetch(`${API_URL}/alerts/user/${userId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch alerts');
  }
  return response.json();
}

async function createAlert(alert: Partial<Alert>, token: string): Promise<Alert> {
  const response = await fetch(`${API_URL}/alerts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(alert),
  });
  if (!response.ok) {
    throw new Error('Failed to create alert');
  }
  return response.json();
}

async function updateAlert(alertId: string, updates: Partial<Alert>, token: string): Promise<Alert> {
  const response = await fetch(`${API_URL}/alerts/${alertId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });
  if (!response.ok) {
    throw new Error('Failed to update alert');
  }
  return response.json();
}

async function deleteAlert(alertId: string, token: string): Promise<void> {
  const response = await fetch(`${API_URL}/alerts/${alertId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to delete alert');
  }
}

export function AlertsManager() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const { data: alerts, isLoading } = useQuery({
    queryKey: ['alerts', user?.uid],
    queryFn: async () => {
      if (!user) throw new Error('Not authenticated');
      const token = await user.getIdToken();
      return fetchAlerts(user.uid, token);
    },
    enabled: !!user,
  });

  const createMutation = useMutation({
    mutationFn: async (alert: Partial<Alert>) => {
      if (!user) throw new Error('Not authenticated');
      const token = await user.getIdToken();
      return createAlert(alert, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', user?.uid] });
      setShowForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ alertId, updates }: { alertId: string; updates: Partial<Alert> }) => {
      if (!user) throw new Error('Not authenticated');
      const token = await user.getIdToken();
      return updateAlert(alertId, updates, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', user?.uid] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (alertId: string) => {
      if (!user) throw new Error('Not authenticated');
      const token = await user.getIdToken();
      return deleteAlert(alertId, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', user?.uid] });
    },
  });

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <Bell className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-2xl font-semibold mb-2">Alerts</h2>
          <p className="text-muted-foreground mb-4">
            Sign in to create custom alerts for blockchain metrics
          </p>
          <Link href="/sign-in">
            <Button>Sign In</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Alerts</h1>
          <p className="text-muted-foreground mt-1">
            Get notified when blockchain metrics meet your conditions
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="w-4 h-4 mr-2" />
          Create Alert
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alert Form */}
        {showForm && (
          <div className="lg:col-span-1">
            <AlertForm
              onSubmit={(alert) => createMutation.mutate(alert)}
              onCancel={() => setShowForm(false)}
              isLoading={createMutation.isPending}
            />
          </div>
        )}

        {/* Alert List */}
        <div className={showForm ? 'lg:col-span-2' : 'lg:col-span-3'}>
          <AlertList
            alerts={alerts || []}
            isLoading={isLoading}
            onToggle={(alertId, isActive) =>
              updateMutation.mutate({ alertId, updates: { is_active: isActive } })
            }
            onDelete={(alertId) => deleteMutation.mutate(alertId)}
          />
        </div>
      </div>
    </div>
  );
}

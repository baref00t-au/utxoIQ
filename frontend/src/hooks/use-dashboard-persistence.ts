'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { DashboardWidget, DashboardConfiguration } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
const AUTOSAVE_DELAY = 2000; // 2 seconds as per requirements

interface UseDashboardPersistenceOptions {
  dashboardId?: string;
  userId?: string;
  enabled?: boolean;
}

interface UseDashboardPersistenceReturn {
  widgets: DashboardWidget[];
  isLoading: boolean;
  isSaving: boolean;
  error: Error | null;
  addWidget: (widget: Omit<DashboardWidget, 'id'>) => void;
  removeWidget: (widgetId: string) => void;
  updateWidgets: (widgets: DashboardWidget[]) => void;
  saveDashboard: () => Promise<void>;
}

export function useDashboardPersistence({
  dashboardId,
  userId,
  enabled = true,
}: UseDashboardPersistenceOptions = {}): UseDashboardPersistenceReturn {
  const [widgets, setWidgets] = useState<DashboardWidget[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pendingChangesRef = useRef(false);

  // Load dashboard from backend
  useEffect(() => {
    if (!enabled || !dashboardId) {
      setIsLoading(false);
      return;
    }

    const loadDashboard = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(
          `${API_URL}/api/v1/dashboards/${dashboardId}`,
          {
            headers: {
              'Content-Type': 'application/json',
              // Add auth token if available
              ...(userId && { 'X-User-ID': userId }),
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to load dashboard');
        }

        const dashboard: DashboardConfiguration = await response.json();
        setWidgets(dashboard.widgets);
        setError(null);
      } catch (err) {
        setError(err as Error);
        console.error('Failed to load dashboard:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboard();
  }, [dashboardId, userId, enabled]);

  // Save dashboard to backend
  const saveDashboard = useCallback(async () => {
    if (!enabled || !dashboardId || widgets.length === 0) {
      return;
    }

    try {
      setIsSaving(true);
      const response = await fetch(
        `${API_URL}/api/v1/dashboards/${dashboardId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            ...(userId && { 'X-User-ID': userId }),
          },
          body: JSON.stringify({
            widgets,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to save dashboard');
      }

      pendingChangesRef.current = false;
      setError(null);
    } catch (err) {
      setError(err as Error);
      console.error('Failed to save dashboard:', err);
    } finally {
      setIsSaving(false);
    }
  }, [dashboardId, userId, widgets, enabled]);

  // Debounced auto-save
  useEffect(() => {
    if (!pendingChangesRef.current || !enabled) {
      return;
    }

    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Set new timeout for auto-save
    saveTimeoutRef.current = setTimeout(() => {
      saveDashboard();
    }, AUTOSAVE_DELAY);

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [widgets, saveDashboard, enabled]);

  // Add widget
  const addWidget = useCallback((widget: Omit<DashboardWidget, 'id'>) => {
    const newWidget: DashboardWidget = {
      ...widget,
      id: `widget-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };

    setWidgets((prev) => [...prev, newWidget]);
    pendingChangesRef.current = true;
  }, []);

  // Remove widget
  const removeWidget = useCallback((widgetId: string) => {
    setWidgets((prev) => prev.filter((w) => w.id !== widgetId));
    pendingChangesRef.current = true;
  }, []);

  // Update widgets (for drag-and-drop and resize)
  const updateWidgets = useCallback((newWidgets: DashboardWidget[]) => {
    setWidgets(newWidgets);
    pendingChangesRef.current = true;
  }, []);

  return {
    widgets,
    isLoading,
    isSaving,
    error,
    addWidget,
    removeWidget,
    updateWidgets,
    saveDashboard,
  };
}

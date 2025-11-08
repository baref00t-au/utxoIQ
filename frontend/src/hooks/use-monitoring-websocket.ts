'use client';

import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface MonitoringMessage {
  type: 'status_update' | 'backfill_update' | 'insight_generated' | 'signal_computed' | 'pong';
  data?: any;
  job_id?: string;
  timestamp: string;
}

interface UseMonitoringWebSocketOptions {
  enabled?: boolean;
  onStatusUpdate?: (data: any) => void;
  onBackfillUpdate?: (jobId: string, data: any) => void;
  onInsightGenerated?: (data: any) => void;
  onSignalComputed?: (data: any) => void;
}

export function useMonitoringWebSocket(options: UseMonitoringWebSocketOptions = {}) {
  const {
    enabled = true,
    onStatusUpdate,
    onBackfillUpdate,
    onInsightGenerated,
    onSignalComputed,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<MonitoringMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!enabled) return;

    const connect = () => {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
      const ws = new WebSocket(`${wsUrl}/ws/monitoring`);

      ws.onopen = () => {
        console.log('Monitoring WebSocket connected');
        setIsConnected(true);

        // Send subscribe message
        ws.send(JSON.stringify({ type: 'subscribe' }));

        // Start ping interval
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }));
          }
        }, 30000); // Ping every 30 seconds

        // Store interval for cleanup
        (ws as any).pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          const message: MonitoringMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Handle different message types
          switch (message.type) {
            case 'status_update':
              if (onStatusUpdate) {
                onStatusUpdate(message.data);
              }
              // Invalidate system status query
              queryClient.invalidateQueries({ queryKey: ['system-status'] });
              break;

            case 'backfill_update':
              if (onBackfillUpdate && message.job_id) {
                onBackfillUpdate(message.job_id, message.data);
              }
              // Invalidate backfill queries
              queryClient.invalidateQueries({ queryKey: ['backfill-progress'] });
              break;

            case 'insight_generated':
              if (onInsightGenerated) {
                onInsightGenerated(message.data);
              }
              // Invalidate insights queries
              queryClient.invalidateQueries({ queryKey: ['insights'] });
              queryClient.invalidateQueries({ queryKey: ['insight-metrics'] });
              break;

            case 'signal_computed':
              if (onSignalComputed) {
                onSignalComputed(message.data);
              }
              // Invalidate signal queries
              queryClient.invalidateQueries({ queryKey: ['signal-metrics'] });
              break;

            case 'pong':
              // Heartbeat response
              break;

            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('Monitoring WebSocket disconnected');
        setIsConnected(false);

        // Clear ping interval
        if ((ws as any).pingInterval) {
          clearInterval((ws as any).pingInterval);
        }

        // Attempt to reconnect after 5 seconds
        if (enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 5000);
        }
      };

      wsRef.current = ws;
    };

    connect();

    // Cleanup
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        if ((wsRef.current as any).pingInterval) {
          clearInterval((wsRef.current as any).pingInterval);
        }
        wsRef.current.close();
      }
    };
  }, [enabled, queryClient, onStatusUpdate, onBackfillUpdate, onInsightGenerated, onSignalComputed]);

  return {
    isConnected,
    lastMessage,
    send: (message: any) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(message));
      }
    },
  };
}

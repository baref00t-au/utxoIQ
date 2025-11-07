/**
 * Alerts resource for utxoIQ API
 */

import type { AxiosInstance } from 'axios';
import type { Alert, CreateAlertParams, UpdateAlertParams } from '../types';

export class AlertsResource {
  constructor(private axios: AxiosInstance) {}

  async list(userId?: string): Promise<Alert[]> {
    const response = await this.axios.get<{ alerts: Alert[] }>('/alerts', {
      params: userId ? { user_id: userId } : undefined,
    });
    return response.data.alerts;
  }

  async create(params: CreateAlertParams): Promise<Alert> {
    const response = await this.axios.post<Alert>('/alerts', {
      signal_type: params.signalType,
      threshold: params.threshold,
      operator: params.operator,
      notification_channel: params.notificationChannel || 'email',
      is_active: params.isActive !== undefined ? params.isActive : true,
    });
    return response.data;
  }

  async get(alertId: string): Promise<Alert> {
    const response = await this.axios.get<Alert>(`/alerts/${alertId}`);
    return response.data;
  }

  async update(alertId: string, params: UpdateAlertParams): Promise<Alert> {
    const payload: any = {};
    if (params.threshold !== undefined) payload.threshold = params.threshold;
    if (params.isActive !== undefined) payload.is_active = params.isActive;
    if (params.notificationChannel !== undefined) {
      payload.notification_channel = params.notificationChannel;
    }

    const response = await this.axios.put<Alert>(`/alerts/${alertId}`, payload);
    return response.data;
  }

  async delete(alertId: string): Promise<boolean> {
    await this.axios.delete(`/alerts/${alertId}`);
    return true;
  }
}

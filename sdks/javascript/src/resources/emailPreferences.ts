/**
 * Email preferences resource for utxoIQ API
 */

import type { AxiosInstance } from 'axios';
import type { EmailPreferences, UpdateEmailPreferencesParams } from '../types';

export class EmailPreferencesResource {
  constructor(private axios: AxiosInstance) {}

  async get(): Promise<EmailPreferences> {
    const response = await this.axios.get<EmailPreferences>('/email/preferences');
    return response.data;
  }

  async update(params: UpdateEmailPreferencesParams): Promise<EmailPreferences> {
    const payload: any = {};
    if (params.dailyBriefEnabled !== undefined) {
      payload.daily_brief_enabled = params.dailyBriefEnabled;
    }
    if (params.frequency !== undefined) payload.frequency = params.frequency;
    if (params.signalFilters !== undefined) payload.signal_filters = params.signalFilters;
    if (params.quietHours !== undefined) payload.quiet_hours = params.quietHours;

    const response = await this.axios.put<EmailPreferences>('/email/preferences', payload);
    return response.data;
  }
}

/**
 * Daily brief resource for utxoIQ API
 */

import type { AxiosInstance } from 'axios';
import type { DailyBrief } from '../types';

export class DailyBriefResource {
  constructor(private axios: AxiosInstance) {}

  async getByDate(date: Date): Promise<DailyBrief> {
    const dateStr = date.toISOString().split('T')[0];
    const response = await this.axios.get<DailyBrief>(`/daily-brief/${dateStr}`);
    return response.data;
  }

  async getLatest(): Promise<DailyBrief> {
    const response = await this.axios.get<DailyBrief>('/daily-brief/latest');
    return response.data;
  }
}

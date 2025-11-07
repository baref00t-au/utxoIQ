/**
 * Insights resource for utxoIQ API
 */

import type { AxiosInstance } from 'axios';
import type {
  Insight,
  GetLatestInsightsParams,
  GetPublicInsightsParams,
  SearchInsightsParams,
} from '../types';

export class InsightsResource {
  constructor(private axios: AxiosInstance) {}

  async getLatest(params: GetLatestInsightsParams = {}): Promise<Insight[]> {
    const response = await this.axios.get<{ insights: Insight[] }>('/insights/latest', {
      params,
    });
    return response.data.insights;
  }

  async getPublic(params: GetPublicInsightsParams = {}): Promise<Insight[]> {
    const response = await this.axios.get<{ insights: Insight[] }>('/insights/public', {
      params: { limit: Math.min(params.limit || 20, 20) },
    });
    return response.data.insights;
  }

  async getById(insightId: string): Promise<Insight> {
    const response = await this.axios.get<Insight>(`/insight/${insightId}`);
    return response.data;
  }

  async search(params: SearchInsightsParams): Promise<Insight[]> {
    const response = await this.axios.get<{ insights: Insight[] }>('/insights/search', {
      params: {
        q: params.query,
        limit: params.limit,
        category: params.category,
      },
    });
    return response.data.insights;
  }
}

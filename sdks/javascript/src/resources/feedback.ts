/**
 * Feedback resource for utxoIQ API
 */

import type { AxiosInstance } from 'axios';
import type { UserFeedback, AccuracyLeaderboard, SubmitFeedbackParams } from '../types';

export class FeedbackResource {
  constructor(private axios: AxiosInstance) {}

  async submit(params: SubmitFeedbackParams): Promise<UserFeedback> {
    const payload: any = { rating: params.rating };
    if (params.comment) payload.comment = params.comment;

    const response = await this.axios.post<UserFeedback>(
      `/insights/${params.insightId}/feedback`,
      payload
    );
    return response.data;
  }

  async getAccuracyLeaderboard(): Promise<AccuracyLeaderboard[]> {
    const response = await this.axios.get<{ leaderboard: AccuracyLeaderboard[] }>(
      '/insights/accuracy-leaderboard'
    );
    return response.data.leaderboard;
  }
}

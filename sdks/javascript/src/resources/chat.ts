/**
 * Chat resource for utxoIQ API
 */

import type { AxiosInstance } from 'axios';
import type { ChatResponse, ChatQueryParams } from '../types';

export class ChatResource {
  constructor(private axios: AxiosInstance) {}

  async query(params: ChatQueryParams): Promise<ChatResponse> {
    const response = await this.axios.post<ChatResponse>('/chat/query', {
      question: params.question,
    });
    return response.data;
  }
}

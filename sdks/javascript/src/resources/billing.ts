/**
 * Billing resource for utxoIQ API
 */

import type { AxiosInstance } from 'axios';
import type { Subscription, CreateCheckoutSessionParams } from '../types';

export class BillingResource {
  constructor(private axios: AxiosInstance) {}

  async getSubscription(): Promise<Subscription> {
    const response = await this.axios.get<Subscription>('/billing/subscription');
    return response.data;
  }

  async createCheckoutSession(params: CreateCheckoutSessionParams): Promise<{ url: string }> {
    const response = await this.axios.post<{ url: string }>('/billing/checkout', {
      tier: params.tier,
      success_url: params.successUrl,
      cancel_url: params.cancelUrl,
    });
    return response.data;
  }

  async cancelSubscription(): Promise<Subscription> {
    const response = await this.axios.post<Subscription>('/billing/cancel');
    return response.data;
  }
}

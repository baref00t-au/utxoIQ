import { Insight, DailyBrief } from '@/types';
import { MOCK_INSIGHTS } from './mock-data';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const USE_MOCK_DATA = process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true';

export async function fetchInsights(limit: number = 20, category?: string): Promise<Insight[]> {
  // Use mock data if backend is unavailable
  if (USE_MOCK_DATA) {
    return Promise.resolve(MOCK_INSIGHTS.slice(0, limit));
  }

  try {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (category) {
      params.append('category', category);
    }

    const response = await fetch(`${API_URL}/insights/latest?${params.toString()}`);
    if (!response.ok) {
      throw new Error('Failed to fetch insights');
    }
    return response.json();
  } catch (error) {
    console.warn('Backend unavailable, using mock data:', error);
    return MOCK_INSIGHTS.slice(0, limit);
  }
}

export async function fetchPublicInsights(): Promise<Insight[]> {
  // Use mock data if backend is unavailable
  if (USE_MOCK_DATA) {
    return Promise.resolve(MOCK_INSIGHTS);
  }

  try {
    const response = await fetch(`${API_URL}/insights/public?limit=20`);
    if (!response.ok) {
      throw new Error('Failed to fetch public insights');
    }
    return response.json();
  } catch (error) {
    console.warn('Backend unavailable, using mock data:', error);
    return MOCK_INSIGHTS;
  }
}

export async function fetchInsightById(id: string): Promise<Insight> {
  // Use mock data if backend is unavailable
  if (USE_MOCK_DATA) {
    const insight = MOCK_INSIGHTS.find(i => i.id === id);
    if (!insight) throw new Error('Insight not found');
    return Promise.resolve(insight);
  }

  try {
    const response = await fetch(`${API_URL}/insight/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch insight');
    }
    return response.json();
  } catch (error) {
    console.warn('Backend unavailable, using mock data:', error);
    const insight = MOCK_INSIGHTS.find(i => i.id === id);
    if (!insight) throw new Error('Insight not found');
    return insight;
  }
}

export async function fetchDailyBrief(date?: string): Promise<DailyBrief> {
  // Use mock data if backend is unavailable
  if (USE_MOCK_DATA) {
    return Promise.resolve({
      date: date || new Date().toISOString().split('T')[0],
      insights: MOCK_INSIGHTS.slice(0, 3),
      summary: 'Today\'s blockchain activity shows increased mempool congestion, significant exchange outflows, and whale accumulation patterns. These signals suggest potential market volatility in the coming hours.',
    });
  }

  try {
    const dateParam = date || new Date().toISOString().split('T')[0];
    const response = await fetch(`${API_URL}/daily-brief/${dateParam}`);
    if (!response.ok) {
      throw new Error('Failed to fetch daily brief');
    }
    return response.json();
  } catch (error) {
    console.warn('Backend unavailable, using mock data:', error);
    return {
      date: date || new Date().toISOString().split('T')[0],
      insights: MOCK_INSIGHTS.slice(0, 3),
      summary: 'Today\'s blockchain activity shows increased mempool congestion, significant exchange outflows, and whale accumulation patterns. These signals suggest potential market volatility in the coming hours.',
    };
  }
}

export async function submitFeedback(insightId: string, rating: 'useful' | 'not_useful', token: string) {
  const response = await fetch(`${API_URL}/insights/${insightId}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ rating }),
  });
  if (!response.ok) {
    throw new Error('Failed to submit feedback');
  }
  return response.json();
}

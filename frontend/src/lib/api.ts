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
    const data = await response.json();
    // API returns {insights: [...], total, page, ...}, extract just the insights array
    return data.insights || [];
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
    const response = await fetch(`${API_URL}/insights/public`);
    if (!response.ok) {
      throw new Error('Failed to fetch public insights');
    }
    const data = await response.json();
    // API returns {insights: [...], total, page, ...}, extract just the insights array
    return data.insights || [];
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

// Monitoring API functions
export async function fetchServiceMetrics(
  serviceName: string,
  timeRange: string = '1h'
): Promise<any> {
  const response = await fetch(
    `${API_URL}/api/v1/monitoring/metrics/${serviceName}?time_range=${timeRange}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch service metrics');
  }
  return response.json();
}

export async function fetchBaseline(metricType: string, days: number = 7): Promise<any> {
  const response = await fetch(
    `${API_URL}/api/v1/monitoring/baseline?metric_type=${metricType}&days=${days}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch baseline');
  }
  return response.json();
}

export async function fetchAlertConfigurations(token: string): Promise<any[]> {
  const response = await fetch(`${API_URL}/api/v1/monitoring/alerts`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch alert configurations');
  }
  return response.json();
}

export async function createAlertConfiguration(data: any, token: string): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/monitoring/alerts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create alert configuration');
  }
  return response.json();
}

export async function updateAlertConfiguration(
  id: string,
  data: any,
  token: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/monitoring/alerts/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update alert configuration');
  }
  return response.json();
}

export async function deleteAlertConfiguration(id: string, token: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/monitoring/alerts/${id}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to delete alert configuration');
  }
}

export async function fetchAlertHistory(
  filters?: {
    service?: string;
    severity?: string;
    start_date?: string;
    end_date?: string;
  },
  token?: string
): Promise<any> {
  const params = new URLSearchParams();
  if (filters?.service) params.append('service', filters.service);
  if (filters?.severity) params.append('severity', filters.severity);
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);

  const headers: HeadersInit = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_URL}/api/v1/monitoring/alerts/history?${params.toString()}`,
    { headers }
  );
  if (!response.ok) {
    throw new Error('Failed to fetch alert history');
  }
  return response.json();
}

export async function fetchDependencyGraph(): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/monitoring/dependencies`);
  if (!response.ok) {
    throw new Error('Failed to fetch dependency graph');
  }
  return response.json();
}

export async function searchLogs(
  query: string,
  filters?: {
    service?: string;
    severity?: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
  }
): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/monitoring/logs/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      ...filters,
    }),
  });
  if (!response.ok) {
    throw new Error('Failed to search logs');
  }
  return response.json();
}

export async function fetchLogContext(logId: string, contextLines: number = 10): Promise<any> {
  const response = await fetch(
    `${API_URL}/api/v1/monitoring/logs/${logId}/context?context_lines=${contextLines}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch log context');
  }
  return response.json();
}

export async function fetchTrace(traceId: string): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/monitoring/traces/${traceId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch trace');
  }
  return response.json();
}

export async function fetchDashboards(token: string): Promise<any[]> {
  const response = await fetch(`${API_URL}/api/v1/monitoring/dashboards`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch dashboards');
  }
  return response.json();
}

export async function createDashboard(data: any, token: string): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/monitoring/dashboards`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create dashboard');
  }
  return response.json();
}

export async function updateDashboard(id: string, data: any, token: string): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/monitoring/dashboards/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update dashboard');
  }
  return response.json();
}

export async function fetchWidgetData(
  dashboardId: string,
  widgetId: string,
  token: string
): Promise<any> {
  const response = await fetch(
    `${API_URL}/api/v1/monitoring/dashboards/${dashboardId}/widget-data/${widgetId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  if (!response.ok) {
    throw new Error('Failed to fetch widget data');
  }
  return response.json();
}

// Filter Presets API functions
export async function fetchFilterPresets(token: string): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/filters/presets`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch filter presets');
  }
  return response.json();
}

export async function createFilterPreset(
  data: { name: string; filters: any },
  token: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/filters/presets`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create filter preset');
  }
  return response.json();
}

export async function updateFilterPreset(
  id: string,
  data: { name?: string; filters?: any },
  token: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/filters/presets/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update filter preset');
  }
  return response.json();
}

export async function deleteFilterPreset(id: string, token: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/filters/presets/${id}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to delete filter preset');
  }
}

// Bookmark API functions
export async function fetchBookmarks(
  token: string,
  folderId?: string,
  limit: number = 100,
  offset: number = 0
): Promise<any> {
  const params = new URLSearchParams();
  if (folderId) params.append('folder_id', folderId);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const response = await fetch(`${API_URL}/api/v1/bookmarks?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch bookmarks');
  }
  return response.json();
}

export async function checkBookmark(insightId: string, token: string): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/bookmarks/check/${insightId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to check bookmark');
  }
  return response.json();
}

export async function createBookmark(
  data: { insight_id: string; folder_id?: string; note?: string },
  token: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/bookmarks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create bookmark');
  }
  return response.json();
}

export async function updateBookmark(
  id: string,
  data: { folder_id?: string; note?: string },
  token: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/bookmarks/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update bookmark');
  }
  return response.json();
}

export async function deleteBookmark(id: string, token: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/bookmarks/${id}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to delete bookmark');
  }
}

// Bookmark Folder API functions
export async function fetchBookmarkFolders(token: string): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/bookmarks/folders`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch bookmark folders');
  }
  return response.json();
}

export async function createBookmarkFolder(
  data: { name: string },
  token: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/bookmarks/folders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create bookmark folder');
  }
  return response.json();
}

export async function updateBookmarkFolder(
  id: string,
  data: { name: string },
  token: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/v1/bookmarks/folders/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update bookmark folder');
  }
  return response.json();
}

export async function deleteBookmarkFolder(id: string, token: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/bookmarks/folders/${id}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to delete bookmark folder');
  }
}

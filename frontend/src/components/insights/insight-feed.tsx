'use client';

import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useWebSocket } from '@/lib/websocket';
import { useDebounce } from '@/hooks/use-debounce';
import { useListNavigation } from '@/hooks/use-insight-feed-shortcuts';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { fetchInsights, fetchPublicInsights } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { InsightCard } from './insight-card';
import { InsightFilters } from './insight-filters';
import { ExportButton } from './export-button';
import { Insight, SignalType, FilterState } from '@/types';
import Link from 'next/link';
import { Loader2 } from 'lucide-react';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export function InsightFeed() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  // Focus search input with "/" shortcut
  const focusSearch = () => {
    const searchInput = document.querySelector('[data-search-input]') as HTMLInputElement;
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    }
  };

  // Initialize filters from URL query params
  const [filters, setFilters] = useState<FilterState>(() => {
    const search = searchParams.get('search') || '';
    const categories = searchParams.get('categories')?.split(',').filter(Boolean) as SignalType[] || [];
    const minConfidence = parseFloat(searchParams.get('minConfidence') || '0');
    const startDate = searchParams.get('startDate');
    const endDate = searchParams.get('endDate');
    
    return {
      search,
      categories,
      minConfidence,
      dateRange: startDate && endDate ? {
        start: new Date(startDate),
        end: new Date(endDate),
      } : null,
    };
  });

  // Debounce filters for performance (300ms delay)
  const debouncedFilters = useDebounce(filters, 300);

  // Update URL query params when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    
    if (debouncedFilters.search) {
      params.set('search', debouncedFilters.search);
    }
    if (debouncedFilters.categories.length > 0) {
      params.set('categories', debouncedFilters.categories.join(','));
    }
    if (debouncedFilters.minConfidence > 0) {
      params.set('minConfidence', debouncedFilters.minConfidence.toString());
    }
    if (debouncedFilters.dateRange) {
      params.set('startDate', debouncedFilters.dateRange.start.toISOString());
      params.set('endDate', debouncedFilters.dateRange.end.toISOString());
    }

    const queryString = params.toString();
    const newUrl = queryString ? `?${queryString}` : window.location.pathname;
    
    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl);
  }, [debouncedFilters]);

  // Fetch initial insights
  const { data: initialInsights, isLoading } = useQuery({
    queryKey: ['insights', user ? 'authenticated' : 'public'],
    queryFn: () => (user ? fetchInsights(50) : fetchPublicInsights()),
    refetchInterval: user ? false : 60000, // Refetch every minute for guest mode
  });

  // WebSocket for real-time updates (authenticated users only)
  const { lastMessage, isConnected } = useWebSocket(
    `${WS_URL}/ws/insights`,
    !!user
  );

  // Initialize insights from query
  useEffect(() => {
    if (initialInsights && Array.isArray(initialInsights)) {
      setInsights(initialInsights);
    }
  }, [initialInsights]);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'new_insight') {
      const newInsight = lastMessage.data as Insight;
      setInsights((prev) => [newInsight, ...prev]);
    }
  }, [lastMessage]);

  // Filter insights with memoization for performance
  const filteredInsights = useMemo(() => {
    if (!Array.isArray(insights)) return [];

    const startTime = performance.now();
    
    const filtered = insights.filter((insight) => {
      // Category filter (AND logic with multiple categories)
      if (debouncedFilters.categories.length > 0 && 
          !debouncedFilters.categories.includes(insight.signal_type)) {
        return false;
      }

      // Confidence filter
      if (insight.confidence < debouncedFilters.minConfidence) {
        return false;
      }

      // Search filter (full-text search in headline and summary)
      if (debouncedFilters.search) {
        const searchLower = debouncedFilters.search.toLowerCase();
        const matchesHeadline = insight.headline.toLowerCase().includes(searchLower);
        const matchesSummary = insight.summary.toLowerCase().includes(searchLower);
        if (!matchesHeadline && !matchesSummary) {
          return false;
        }
      }

      // Date range filter
      if (debouncedFilters.dateRange) {
        const insightDate = new Date(insight.timestamp);
        if (insightDate < debouncedFilters.dateRange.start || 
            insightDate > debouncedFilters.dateRange.end) {
          return false;
        }
      }

      return true;
    });

    const endTime = performance.now();
    const filterTime = endTime - startTime;
    
    // Log warning if filtering takes longer than 500ms (requirement)
    if (filterTime > 500) {
      console.warn(`Filter application took ${filterTime.toFixed(2)}ms (exceeds 500ms requirement)`);
    }

    return filtered;
  }, [insights, debouncedFilters]);

  // Keyboard shortcuts for authenticated users
  useKeyboardShortcuts(
    user
      ? [
          {
            key: '/',
            action: focusSearch,
            description: 'Focus search input',
            category: 'Navigation',
          },
        ]
      : [],
    { enabled: !!user }
  );

  // Arrow key navigation for insight cards
  useListNavigation(filteredInsights.length);

  // Show loading spinner while auth is initializing
  if (authLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-brand" />
      </div>
    );
  }

  // Guest Mode: Show sign-up prompt if not authenticated
  if (!user) {
    return (
      <div className="space-y-6">
        <div className="rounded-lg border-2 border-brand/20 bg-card p-6 text-center">
          <h2 className="text-2xl font-semibold mb-2">Welcome to utxoIQ</h2>
          <p className="text-muted-foreground mb-4">
            Sign in to access real-time Bitcoin blockchain insights powered by AI
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/sign-in">
              <Button>Sign In</Button>
            </Link>
            <Link href="/sign-up">
              <Button variant="outline">Create Account</Button>
            </Link>
          </div>
        </div>
        <div className="text-center text-sm text-muted-foreground">
          <p>Preview: Showing 20 most recent public insights</p>
        </div>
        {/* Guest Mode Feed - Limited to 20 insights */}
        <div className="space-y-4">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-brand" />
            </div>
          ) : filteredInsights.length === 0 ? (
            <div className="rounded-lg border border-border bg-card p-8 text-center">
              <p className="text-muted-foreground">No insights available yet</p>
            </div>
          ) : (
            filteredInsights.map((insight) => (
              <InsightCard key={insight.id} insight={insight} isGuest={true} />
            ))
          )}
        </div>
        {/* Conversion prompt at bottom */}
        <div className="rounded-lg border border-border bg-card p-6 text-center">
          <p className="text-sm text-muted-foreground mb-3">
            Want to see more? Create a free account to access:
          </p>
          <ul className="text-sm text-left max-w-md mx-auto mb-4 space-y-1">
            <li>✓ Real-time insight streaming</li>
            <li>✓ Custom alerts and notifications</li>
            <li>✓ AI-powered chat interface</li>
            <li>✓ Full insight history</li>
          </ul>
          <Link href="/sign-up">
            <Button>Create Free Account</Button>
          </Link>
        </div>
      </div>
    );
  }

  // Authenticated Feed
  return (
    <div className="flex gap-6">
      {/* Left sidebar - Filters */}
      <aside className="hidden lg:block w-64 flex-shrink-0">
        <div className="sticky top-20">
          <InsightFilters
            filters={filters}
            onFiltersChange={setFilters}
            resultCount={filteredInsights.length}
          />
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Live Feed</h1>
            {isConnected && (
              <p className="text-sm text-muted-foreground mt-1">
                <span className="inline-block w-2 h-2 bg-success rounded-full mr-2 animate-pulse" />
                Connected - Real-time updates enabled
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <ExportButton
              filters={{
                signal_type: debouncedFilters.categories[0],
                min_confidence: debouncedFilters.minConfidence,
                date_range: debouncedFilters.dateRange ? {
                  start: debouncedFilters.dateRange.start.toISOString(),
                  end: debouncedFilters.dateRange.end.toISOString(),
                } : undefined,
              }}
              limit={1000}
              disabled={filteredInsights.length === 0}
            />
            <Button
              variant="outline"
              size="sm"
              className="lg:hidden"
              onClick={() => setShowFilters(!showFilters)}
            >
              Filters
            </Button>
          </div>
        </div>

        {/* Mobile filters */}
        {showFilters && (
          <div className="lg:hidden">
            <InsightFilters
              filters={filters}
              onFiltersChange={setFilters}
              resultCount={filteredInsights.length}
            />
          </div>
        )}

        <div className="space-y-4">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-brand" />
            </div>
          ) : filteredInsights.length === 0 ? (
            <div className="rounded-lg border border-border bg-card p-8 text-center">
              <p className="text-muted-foreground">
                {insights.length === 0
                  ? 'No insights yet. New insights will appear here in real-time.'
                  : 'No insights match your filters.'}
              </p>
            </div>
          ) : (
            filteredInsights.map((insight) => (
              <InsightCard key={insight.id} insight={insight} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { useWebSocket } from '@/lib/websocket';
import { fetchInsights, fetchPublicInsights } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { InsightCard } from './insight-card';
import { InsightFilters } from './insight-filters';
import { Insight, SignalType } from '@/types';
import Link from 'next/link';
import { Loader2 } from 'lucide-react';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export function InsightFeed() {
  const { user } = useAuth();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<SignalType | 'all'>('all');
  const [highConfidenceOnly, setHighConfidenceOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);

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
    if (initialInsights) {
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

  // Filter insights
  const filteredInsights = insights.filter((insight) => {
    if (selectedCategory !== 'all' && insight.signal_type !== selectedCategory) {
      return false;
    }
    if (highConfidenceOnly && insight.confidence < 0.7) {
      return false;
    }
    if (searchQuery && !insight.headline.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

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
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            highConfidenceOnly={highConfidenceOnly}
            onHighConfidenceChange={setHighConfidenceOnly}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
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
              selectedCategory={selectedCategory}
              onCategoryChange={setSelectedCategory}
              highConfidenceOnly={highConfidenceOnly}
              onHighConfidenceChange={setHighConfidenceOnly}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
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

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchDailyBrief } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { BriefCard } from './brief-card';
import { Loader2, ChevronLeft, ChevronRight, Share2, Zap } from 'lucide-react';
import { formatDate } from '@/lib/utils';

export function DailyBriefView() {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  const { data: brief, isLoading } = useQuery({
    queryKey: ['daily-brief', selectedDate.toISOString().split('T')[0]],
    queryFn: () => fetchDailyBrief(selectedDate.toISOString().split('T')[0]),
  });

  const handlePreviousDay = () => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() - 1);
    setSelectedDate(newDate);
  };

  const handleNextDay = () => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + 1);
    if (newDate <= new Date()) {
      setSelectedDate(newDate);
    }
  };

  const handleShare = () => {
    const url = `${window.location.origin}/brief?date=${selectedDate.toISOString().split('T')[0]}`;
    navigator.clipboard.writeText(url);
  };

  const isToday = selectedDate.toDateString() === new Date().toDateString();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Zap className="w-8 h-8 text-brand" />
          <div>
            <h1 className="text-3xl font-bold">Daily Brief</h1>
            <p className="text-sm text-muted-foreground">07:00 UTC</p>
          </div>
        </div>

        {/* Date Navigation */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePreviousDay}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <div className="px-4 py-2 rounded-lg bg-card border border-border">
              <span className="font-medium">{formatDate(selectedDate)}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleNextDay}
              disabled={isToday}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
          <Button variant="outline" size="sm" onClick={handleShare}>
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-brand" />
        </div>
      ) : !brief || brief.insights.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <p className="text-muted-foreground">
            No brief available for this date
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Summary */}
          {brief.summary && (
            <div className="rounded-2xl border border-border bg-card p-6">
              <h2 className="text-xl font-semibold mb-3">Overview</h2>
              <p className="text-muted-foreground leading-relaxed">
                {brief.summary}
              </p>
            </div>
          )}

          {/* Top Events */}
          <div>
            <h2 className="text-xl font-semibold mb-4">
              Top {brief.insights.length} Events
            </h2>
            <div className="space-y-4">
              {brief.insights.map((insight, idx) => (
                <BriefCard key={insight.id} insight={insight} rank={idx + 1} />
              ))}
            </div>
          </div>

          {/* Public Preview Banner */}
          <div className="rounded-2xl border-2 border-brand/20 bg-card p-6 text-center">
            <h3 className="text-lg font-semibold mb-2">
              Get Daily Briefs Delivered
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              Subscribe to receive the Daily Brief in your inbox every morning at 07:00 UTC
            </p>
            <div className="flex gap-3 justify-center">
              <Button>Subscribe to Email</Button>
              <Button variant="outline" asChild>
                <a
                  href="https://twitter.com/utxoiq"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Follow on X
                </a>
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

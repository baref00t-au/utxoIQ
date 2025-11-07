'use client';

import { Insight } from '@/types';
import { formatTime, cn } from '@/lib/utils';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TrendingUp } from 'lucide-react';

interface BriefCardProps {
  insight: Insight;
  rank: number;
}

const categoryColors = {
  mempool: 'hsl(var(--mempool))',
  exchange: 'hsl(var(--exchange))',
  miner: 'hsl(var(--miner))',
  whale: 'hsl(var(--whale))',
};

const categoryLabels = {
  mempool: 'MEMPOOL',
  exchange: 'EXCHANGE',
  miner: 'MINER',
  whale: 'WHALE',
};

export function BriefCard({ insight, rank }: BriefCardProps) {
  const confidenceColor =
    insight.confidence >= 0.85
      ? 'text-success'
      : insight.confidence >= 0.7
      ? 'text-warning'
      : 'text-muted-foreground';

  const categoryColor = categoryColors[insight.signal_type];

  return (
    <div className="rounded-2xl border border-border bg-card p-6 hover:shadow-md transition-all">
      <div className="flex gap-4">
        {/* Rank Badge */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 rounded-full bg-brand/10 flex items-center justify-center">
            <span className="text-xl font-bold text-brand">#{rank}</span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-3">
          {/* Header */}
          <div className="flex items-center gap-2 flex-wrap">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: categoryColor }}
            />
            <span className="text-xs font-medium uppercase tracking-wide">
              {categoryLabels[insight.signal_type]}
            </span>
            <span className="text-xs text-muted-foreground">
              {formatTime(insight.timestamp)}
            </span>
            <Badge variant="outline" className={cn('text-xs', confidenceColor)}>
              {Math.round(insight.confidence * 100)}%
            </Badge>
            {insight.is_predictive && (
              <Badge variant="outline" className="text-xs">
                <TrendingUp className="w-3 h-3 mr-1" />
                Predictive
              </Badge>
            )}
          </div>

          {/* Title */}
          <h3 className="text-lg font-semibold">{insight.headline}</h3>

          {/* Summary */}
          <p className="text-sm text-muted-foreground line-clamp-2">
            {insight.summary}
          </p>

          {/* Action */}
          <Link href={`/insight/${insight.id}`}>
            <Button variant="ghost" size="sm">
              Read More
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

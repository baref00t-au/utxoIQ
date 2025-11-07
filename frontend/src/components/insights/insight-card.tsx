'use client';

import { Insight } from '@/types';
import { formatTime } from '@/lib/utils';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Share2, TrendingUp, TrendingDown } from 'lucide-react';

interface InsightCardProps {
  insight: Insight;
  isGuest?: boolean;
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

export function InsightCard({ insight, isGuest = false }: InsightCardProps) {
  const confidenceColor =
    insight.confidence >= 0.85
      ? 'text-success'
      : insight.confidence >= 0.7
      ? 'text-warning'
      : 'text-muted-foreground';

  const categoryColor = categoryColors[insight.signal_type];

  return (
    <div className="rounded-2xl border border-border bg-card p-6 transition-all hover:shadow-md hover:-translate-y-0.5">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
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
          {insight.is_predictive && (
            <Badge variant="outline" className="text-xs">
              <TrendingUp className="w-3 h-3 mr-1" />
              Predictive
            </Badge>
          )}
        </div>
        <Badge variant="outline" className={cn('text-xs', confidenceColor)}>
          {Math.round(insight.confidence * 100)}% confidence
        </Badge>
      </div>

      {/* Title */}
      <h3 className="text-lg font-semibold mb-2 line-clamp-2">
        {insight.headline}
      </h3>

      {/* Summary */}
      <p className="text-sm text-muted-foreground mb-4 line-clamp-3">
        {insight.summary}
      </p>

      {/* Chart */}
      {insight.chart_url && (
        <div className="mb-4 rounded-lg overflow-hidden bg-background">
          <Image
            src={insight.chart_url}
            alt={`Chart for ${insight.headline}`}
            width={800}
            height={300}
            className="w-full h-auto"
          />
        </div>
      )}

      {/* Evidence */}
      {insight.evidence && insight.evidence.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {insight.evidence.slice(0, 3).map((evidence, idx) => (
            <Badge key={idx} variant="secondary" className="text-xs font-mono">
              {evidence.type}: {evidence.id.slice(0, 8)}...
            </Badge>
          ))}
          {insight.evidence.length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{insight.evidence.length - 3} more
            </Badge>
          )}
        </div>
      )}

      {/* Accuracy Rating */}
      {insight.accuracy_rating !== undefined && (
        <div className="flex items-center gap-2 mb-4 text-xs text-muted-foreground">
          <span>Community accuracy:</span>
          <span className="font-medium text-foreground">
            {Math.round(insight.accuracy_rating * 100)}%
          </span>
          <span>({insight.accuracy_rating > 0.5 ? 'Useful' : 'Mixed'})</span>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-border">
        <Link href={`/insight/${insight.id}`}>
          <Button variant="ghost" size="sm">
            View Details
          </Button>
        </Link>
        <Button variant="ghost" size="sm">
          <Share2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Guest Mode CTA */}
      {isGuest && (
        <div className="mt-4 pt-4 border-t border-border">
          <p className="text-xs text-muted-foreground text-center">
            <Link href="/sign-up" className="text-brand hover:underline">
              Sign up
            </Link>{' '}
            to see full details and set alerts
          </p>
        </div>
      )}
    </div>
  );
}

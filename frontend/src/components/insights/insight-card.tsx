'use client';

import { Insight } from '@/types';
import { formatTime } from '@/lib/utils';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Share2, TrendingUp, TrendingDown } from 'lucide-react';
import { BookmarkButton } from './bookmark-button';

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
    <article 
      className="rounded-2xl border border-border bg-card p-4 sm:p-6 transition-all hover:shadow-md hover:-translate-y-0.5 focus-within:outline-none focus-within:ring-2 focus-within:ring-brand focus-within:ring-offset-2"
      data-insight-card
      aria-labelledby={`insight-title-${insight.id}`}
      aria-describedby={`insight-summary-${insight.id}`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <div
            className="w-3 h-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: categoryColor }}
            role="img"
            aria-label={`${categoryLabels[insight.signal_type]} category indicator`}
          />
          <span className="text-xs font-medium uppercase tracking-wide">
            {categoryLabels[insight.signal_type]}
          </span>
          <time className="text-xs text-muted-foreground" dateTime={insight.timestamp}>
            {formatTime(insight.timestamp)}
          </time>
          {insight.is_predictive && (
            <Badge variant="outline" className="text-xs">
              <TrendingUp className="w-3 h-3 mr-1" aria-hidden="true" />
              Predictive
            </Badge>
          )}
        </div>
        <Badge variant="outline" className={cn('text-xs w-fit', confidenceColor)} aria-label={`Confidence score: ${Math.round(insight.confidence * 100)} percent`}>
          {Math.round(insight.confidence * 100)}% confidence
        </Badge>
      </div>

      {/* Title */}
      <h3 id={`insight-title-${insight.id}`} className="text-lg font-semibold mb-2 line-clamp-2">
        {insight.headline}
      </h3>

      {/* Summary */}
      <p id={`insight-summary-${insight.id}`} className="text-sm text-muted-foreground mb-4 line-clamp-3">
        {insight.summary}
      </p>

      {/* Chart */}
      {insight.chart_url && (
        <figure className="mb-4 rounded-lg overflow-hidden bg-background">
          <Image
            src={insight.chart_url}
            alt={`Chart visualization for ${insight.headline}`}
            width={800}
            height={300}
            className="w-full h-auto"
          />
        </figure>
      )}

      {/* Evidence */}
      {insight.evidence && insight.evidence.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4" role="list" aria-label="Blockchain evidence">
          {insight.evidence.slice(0, 3).map((evidence, idx) => (
            <Badge key={idx} variant="secondary" className="text-xs font-mono" role="listitem">
              <span className="sr-only">{evidence.type} identifier:</span>
              {evidence.type}: {evidence.id.slice(0, 8)}...
            </Badge>
          ))}
          {insight.evidence.length > 3 && (
            <Badge variant="secondary" className="text-xs" role="listitem">
              +{insight.evidence.length - 3} more
            </Badge>
          )}
        </div>
      )}

      {/* Accuracy Rating */}
      {insight.accuracy_rating !== undefined && (
        <div className="flex items-center gap-2 mb-4 text-xs text-muted-foreground" role="status" aria-label={`Community accuracy rating: ${Math.round(insight.accuracy_rating * 100)} percent`}>
          <span>Community accuracy:</span>
          <span className="font-medium text-foreground">
            {Math.round(insight.accuracy_rating * 100)}%
          </span>
          <span>({insight.accuracy_rating > 0.5 ? 'Useful' : 'Mixed'})</span>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-border">
        <Link href={`/insight/${insight.id}`} className="focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded-lg">
          <Button variant="ghost" size="sm" aria-label={`View full details for ${insight.headline}`}>
            View Details
          </Button>
        </Link>
        <div className="flex items-center gap-1" role="group" aria-label="Insight actions">
          {!isGuest && <BookmarkButton insightId={insight.id} />}
          <Button variant="ghost" size="sm" aria-label={`Share ${insight.headline}`}>
            <Share2 className="w-4 h-4" aria-hidden="true" />
          </Button>
        </div>
      </div>

      {/* Guest Mode CTA */}
      {isGuest && (
        <div className="mt-4 pt-4 border-t border-border">
          <p className="text-xs text-muted-foreground text-center">
            <Link href="/sign-up" className="text-brand hover:underline focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded">
              Sign up
            </Link>{' '}
            to see full details and set alerts
          </p>
        </div>
      )}
    </article>
  );
}

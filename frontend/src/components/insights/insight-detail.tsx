'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { fetchInsightById, submitFeedback } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ExplainabilityPanel } from './explainability-panel';
import { FeedbackWidget } from './feedback-widget';
import { formatDate, cn } from '@/lib/utils';
import { Loader2, Share2, Copy, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';

interface InsightDetailProps {
  insightId: string;
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

export function InsightDetail({ insightId }: InsightDetailProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [showExplainability, setShowExplainability] = useState(false);
  const [copiedEvidence, setCopiedEvidence] = useState<string | null>(null);

  const { data: insight, isLoading, error } = useQuery({
    queryKey: ['insight', insightId],
    queryFn: () => fetchInsightById(insightId),
  });

  const feedbackMutation = useMutation({
    mutationFn: async (rating: 'useful' | 'not_useful') => {
      if (!user) throw new Error('Must be logged in');
      const token = await user.getIdToken();
      return submitFeedback(insightId, rating, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insight', insightId] });
    },
  });

  const handleCopyEvidence = (evidenceId: string) => {
    navigator.clipboard.writeText(evidenceId);
    setCopiedEvidence(evidenceId);
    setTimeout(() => setCopiedEvidence(null), 2000);
  };

  const handleShare = () => {
    const url = `${window.location.origin}/insight/${insightId}`;
    navigator.clipboard.writeText(url);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-brand" />
      </div>
    );
  }

  if (error || !insight) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 text-center">
        <p className="text-muted-foreground">Failed to load insight</p>
        <Link href="/">
          <Button variant="outline" className="mt-4">
            Back to Feed
          </Button>
        </Link>
      </div>
    );
  }

  const confidenceColor =
    insight.confidence >= 0.85
      ? 'text-success'
      : insight.confidence >= 0.7
      ? 'text-warning'
      : 'text-muted-foreground';

  const categoryColor = categoryColors[insight.signal_type];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: categoryColor }}
          />
          <span className="text-sm font-medium uppercase tracking-wide">
            {categoryLabels[insight.signal_type]}
          </span>
          <span className="text-sm text-muted-foreground">|</span>
          <span className="text-sm text-muted-foreground">
            {formatDate(insight.timestamp)}
          </span>
          <span className="text-sm text-muted-foreground">|</span>
          <Badge variant="outline" className={cn('text-sm', confidenceColor)}>
            {Math.round(insight.confidence * 100)}% confidence
          </Badge>
        </div>

        <h1 className="text-4xl font-bold">{insight.headline}</h1>

        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" onClick={handleShare}>
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
          {user && (
            <FeedbackWidget
              insightId={insightId}
              onFeedback={(rating) => feedbackMutation.mutate(rating)}
              isLoading={feedbackMutation.isPending}
            />
          )}
        </div>
      </div>

      <Separator />

      {/* Chart */}
      {insight.chart_url && (
        <div className="rounded-2xl overflow-hidden bg-background border border-border">
          <Image
            src={insight.chart_url}
            alt={`Chart for ${insight.headline}`}
            width={1200}
            height={630}
            className="w-full h-auto"
            priority
          />
        </div>
      )}

      {/* Summary */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <h2 className="text-xl font-semibold mb-4">Summary</h2>
        <p className="text-muted-foreground leading-relaxed">{insight.summary}</p>
      </div>

      {/* Explainability */}
      {insight.explainability && (
        <div className="rounded-2xl border border-border bg-card">
          <button
            onClick={() => setShowExplainability(!showExplainability)}
            className="w-full p-6 flex items-center justify-between hover:bg-accent/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold">Why {Math.round(insight.confidence * 100)}% confidence?</h2>
              <Badge variant="secondary">AI Explainability</Badge>
            </div>
            {showExplainability ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
          {showExplainability && (
            <div className="px-6 pb-6">
              <ExplainabilityPanel explainability={insight.explainability} />
            </div>
          )}
        </div>
      )}

      {/* Evidence */}
      {insight.evidence && insight.evidence.length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="text-xl font-semibold mb-4">Evidence</h2>
          <div className="space-y-3">
            {insight.evidence.map((evidence, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-4 rounded-lg bg-background border border-border"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="secondary" className="text-xs uppercase">
                      {evidence.type}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {evidence.description}
                    </span>
                  </div>
                  <code className="text-sm font-mono text-foreground">
                    {evidence.id}
                  </code>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleCopyEvidence(evidence.id)}
                  >
                    {copiedEvidence === evidence.id ? (
                      <span className="text-xs text-success">Copied!</span>
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                  {evidence.url && (
                    <Button variant="ghost" size="sm" asChild>
                      <a href={evidence.url} target="_blank" rel="noopener noreferrer">
                        View
                      </a>
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Accuracy Rating */}
      {insight.accuracy_rating !== undefined && (
        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="text-xl font-semibold mb-4">Community Feedback</h2>
          <div className="flex items-center gap-4">
            <div className="text-3xl font-bold text-brand">
              {Math.round(insight.accuracy_rating * 100)}%
            </div>
            <div className="text-sm text-muted-foreground">
              <p>Users found this insight {insight.accuracy_rating > 0.5 ? 'useful' : 'mixed'}</p>
              <p className="text-xs mt-1">Based on community ratings</p>
            </div>
          </div>
        </div>
      )}

      {/* Back to Feed */}
      <div className="flex justify-center pt-6">
        <Link href="/">
          <Button variant="outline">Back to Feed</Button>
        </Link>
      </div>
    </div>
  );
}

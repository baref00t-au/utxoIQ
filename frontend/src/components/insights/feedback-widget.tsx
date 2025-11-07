'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ThumbsUp, ThumbsDown, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FeedbackWidgetProps {
  insightId: string;
  onFeedback: (rating: 'useful' | 'not_useful') => void;
  isLoading?: boolean;
}

export function FeedbackWidget({ insightId, onFeedback, isLoading }: FeedbackWidgetProps) {
  const [selectedRating, setSelectedRating] = useState<'useful' | 'not_useful' | null>(null);

  const handleFeedback = (rating: 'useful' | 'not_useful') => {
    setSelectedRating(rating);
    onFeedback(rating);
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Submitting feedback...</span>
      </div>
    );
  }

  if (selectedRating) {
    return (
      <div className="flex items-center gap-2 text-sm text-success">
        <span>Thanks for your feedback!</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">Was this useful?</span>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleFeedback('useful')}
        className={cn(
          'gap-2',
          selectedRating === 'useful' && 'border-success text-success'
        )}
      >
        <ThumbsUp className="w-4 h-4" />
        Useful
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleFeedback('not_useful')}
        className={cn(
          'gap-2',
          selectedRating === 'not_useful' && 'border-destructive text-destructive'
        )}
      >
        <ThumbsDown className="w-4 h-4" />
        Not Useful
      </Button>
    </div>
  );
}

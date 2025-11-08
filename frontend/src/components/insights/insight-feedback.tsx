'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Star, MessageSquare, Flag, ThumbsUp } from 'lucide-react';
import { toast } from '@/lib/toast';

interface InsightFeedbackProps {
  insightId: string;
}

interface FeedbackStats {
  insight_id: string;
  total_ratings: number;
  avg_rating: number;
  rating_distribution: Record<string, number>;
  total_comments: number;
  total_flags: number;
}

export function InsightFeedback({ insightId }: InsightFeedbackProps) {
  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [comment, setComment] = useState('');
  const [flagReason, setFlagReason] = useState('');
  const [flagDetails, setFlagDetails] = useState('');
  const queryClient = useQueryClient();

  // Fetch feedback stats
  const { data: stats } = useQuery<FeedbackStats>({
    queryKey: ['feedback-stats', insightId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/feedback/insights/${insightId}/stats`);
      if (!res.ok) throw new Error('Failed to fetch stats');
      return res.json();
    },
  });

  // Rate insight mutation
  const rateMutation = useMutation({
    mutationFn: async ({ rating, comment }: { rating: number; comment?: string }) => {
      const res = await fetch(`/api/v1/feedback/insights/${insightId}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, comment }),
      });
      if (!res.ok) throw new Error('Failed to submit rating');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feedback-stats', insightId] });
      toast.success('Thank you for your feedback!');
      setRating(0);
      setComment('');
    },
    onError: () => {
      toast.error('Failed to submit feedback');
    },
  });

  // Flag insight mutation
  const flagMutation = useMutation({
    mutationFn: async ({ reason, details }: { reason: string; details?: string }) => {
      const res = await fetch(`/api/v1/feedback/insights/${insightId}/flag`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason, details }),
      });
      if (!res.ok) throw new Error('Failed to flag insight');
      return res.json();
    },
    onSuccess: () => {
      toast.success('Thank you for reporting. We\'ll review this shortly.');
      setFlagReason('');
      setFlagDetails('');
    },
    onError: () => {
      toast.error('Failed to submit report');
    },
  });

  const handleRatingSubmit = () => {
    if (rating === 0) {
      toast.error('Please select a rating');
      return;
    }
    rateMutation.mutate({ rating, comment: comment || undefined });
  };

  const handleFlagSubmit = () => {
    if (!flagReason) {
      toast.error('Please select a reason');
      return;
    }
    flagMutation.mutate({ reason: flagReason, details: flagDetails || undefined });
  };

  return (
    <div className="space-y-4">
      {/* Feedback Stats */}
      {stats && stats.total_ratings > 0 && (
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1">
            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
            <span className="font-medium">{stats.avg_rating.toFixed(1)}</span>
            <span className="text-muted-foreground">({stats.total_ratings} ratings)</span>
          </div>
          {stats.total_comments > 0 && (
            <div className="flex items-center gap-1 text-muted-foreground">
              <MessageSquare className="h-4 w-4" />
              <span>{stats.total_comments} comments</span>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2">
        {/* Rate Dialog */}
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              <Star className="h-4 w-4 mr-1" />
              Rate
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Rate this insight</DialogTitle>
              <DialogDescription>
                Help us improve by rating the accuracy and usefulness of this insight
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              {/* Star Rating */}
              <div className="flex justify-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHoveredRating(star)}
                    onMouseLeave={() => setHoveredRating(0)}
                    className="transition-transform hover:scale-110"
                  >
                    <Star
                      className={`h-8 w-8 ${
                        star <= (hoveredRating || rating)
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  </button>
                ))}
              </div>

              {/* Optional Comment */}
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Comment (optional)
                </label>
                <Textarea
                  placeholder="Share your thoughts..."
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  maxLength={1000}
                  rows={3}
                />
              </div>

              <Button
                onClick={handleRatingSubmit}
                disabled={rating === 0 || rateMutation.isPending}
                className="w-full"
              >
                {rateMutation.isPending ? 'Submitting...' : 'Submit Rating'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Flag Dialog */}
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              <Flag className="h-4 w-4 mr-1" />
              Report
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Report this insight</DialogTitle>
              <DialogDescription>
                Let us know if there's an issue with this insight
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              {/* Reason Select */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Reason</label>
                <Select value={flagReason} onValueChange={setFlagReason}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a reason" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="inaccurate">Inaccurate information</SelectItem>
                    <SelectItem value="misleading">Misleading</SelectItem>
                    <SelectItem value="spam">Spam</SelectItem>
                    <SelectItem value="inappropriate">Inappropriate</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Details */}
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Details (optional)
                </label>
                <Textarea
                  placeholder="Provide more context..."
                  value={flagDetails}
                  onChange={(e) => setFlagDetails(e.target.value)}
                  maxLength={500}
                  rows={3}
                />
              </div>

              <Button
                onClick={handleFlagSubmit}
                disabled={!flagReason || flagMutation.isPending}
                className="w-full"
                variant="destructive"
              >
                {flagMutation.isPending ? 'Submitting...' : 'Submit Report'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Quick Helpful Button */}
        <Button variant="ghost" size="sm">
          <ThumbsUp className="h-4 w-4 mr-1" />
          Helpful
        </Button>
      </div>
    </div>
  );
}

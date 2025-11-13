'use client';

import { useState, useEffect } from 'react';
import { Bookmark, BookmarkCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { checkBookmark, createBookmark, deleteBookmark } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

interface BookmarkButtonProps {
  insightId: string;
  size?: 'sm' | 'default' | 'lg';
  variant?: 'ghost' | 'outline' | 'default';
}

export function BookmarkButton({ 
  insightId, 
  size = 'sm', 
  variant = 'ghost' 
}: BookmarkButtonProps) {
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [bookmarkId, setBookmarkId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const { user, getIdToken } = useAuth();

  useEffect(() => {
    if (user) {
      checkBookmarkStatus();
    }
  }, [user, insightId]);

  const checkBookmarkStatus = async () => {
    if (!user) return;

    try {
      const token = await getIdToken();
      const result = await checkBookmark(insightId, token);
      setIsBookmarked(result.exists);
      setBookmarkId(result.bookmark_id);
    } catch (error) {
      console.error('Failed to check bookmark status:', error);
    }
  };

  const handleToggleBookmark = async () => {
    if (!user) {
      toast({
        title: 'Sign in required',
        description: 'Please sign in to bookmark insights',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);

    try {
      const token = await getIdToken();

      if (isBookmarked && bookmarkId) {
        // Remove bookmark
        await deleteBookmark(bookmarkId, token);
        setIsBookmarked(false);
        setBookmarkId(null);
        toast({
          title: 'Bookmark removed',
          description: 'Insight removed from bookmarks',
        });
      } else {
        // Add bookmark
        const result = await createBookmark({ insight_id: insightId }, token);
        setIsBookmarked(true);
        setBookmarkId(result.id);
        toast({
          title: 'Bookmark added',
          description: 'Insight saved to bookmarks',
        });
      }
    } catch (error) {
      console.error('Failed to toggle bookmark:', error);
      toast({
        title: 'Error',
        description: 'Failed to update bookmark',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleToggleBookmark}
      disabled={isLoading}
      aria-label={isBookmarked ? 'Remove bookmark' : 'Add bookmark'}
    >
      {isBookmarked ? (
        <BookmarkCheck className="w-4 h-4" />
      ) : (
        <Bookmark className="w-4 h-4" />
      )}
    </Button>
  );
}

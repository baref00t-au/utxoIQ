'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { updateBookmark } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface BookmarkNoteEditorProps {
  bookmarkId: string;
  currentNote?: string;
  onClose: () => void;
  onSaved: () => void;
}

export function BookmarkNoteEditor({
  bookmarkId,
  currentNote = '',
  onClose,
  onSaved,
}: BookmarkNoteEditorProps) {
  const { getIdToken } = useAuth();
  const { toast } = useToast();
  const [note, setNote] = useState(currentNote);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const token = await getIdToken();
      await updateBookmark(bookmarkId, { note }, token);
      toast({
        title: 'Note saved',
        description: 'Bookmark note updated successfully',
      });
      onSaved();
      onClose();
    } catch (error) {
      console.error('Failed to save note:', error);
      toast({
        title: 'Error',
        description: 'Failed to save note',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Edit Bookmark Note</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <Textarea
            placeholder="Add a note about this insight..."
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={6}
            maxLength={1000}
          />
          <p className="text-xs text-muted-foreground text-right">
            {note.length}/1000 characters
          </p>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Note'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

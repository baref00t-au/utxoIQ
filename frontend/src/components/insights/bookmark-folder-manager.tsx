'use client';

import { useState } from 'react';
import { BookmarkFolder } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Trash2, Edit2, Plus, Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { createBookmarkFolder, updateBookmarkFolder, deleteBookmarkFolder } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface BookmarkFolderManagerProps {
  folders: BookmarkFolder[];
  onClose: () => void;
  onFolderCreated: () => void;
}

export function BookmarkFolderManager({
  folders,
  onClose,
  onFolderCreated,
}: BookmarkFolderManagerProps) {
  const { getIdToken } = useAuth();
  const { toast } = useToast();
  const [newFolderName, setNewFolderName] = useState('');
  const [editingFolder, setEditingFolder] = useState<BookmarkFolder | null>(null);
  const [editName, setEditName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      toast({
        title: 'Error',
        description: 'Folder name cannot be empty',
        variant: 'destructive',
      });
      return;
    }

    setIsCreating(true);
    try {
      const token = await getIdToken();
      await createBookmarkFolder({ name: newFolderName }, token);
      setNewFolderName('');
      toast({
        title: 'Folder created',
        description: 'Bookmark folder created successfully',
      });
      onFolderCreated();
    } catch (error) {
      console.error('Failed to create folder:', error);
      toast({
        title: 'Error',
        description: 'Failed to create folder',
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateFolder = async () => {
    if (!editingFolder || !editName.trim()) return;

    setIsUpdating(true);
    try {
      const token = await getIdToken();
      await updateBookmarkFolder(editingFolder.id, { name: editName }, token);
      setEditingFolder(null);
      setEditName('');
      toast({
        title: 'Folder updated',
        description: 'Folder name updated successfully',
      });
      onFolderCreated();
    } catch (error) {
      console.error('Failed to update folder:', error);
      toast({
        title: 'Error',
        description: 'Failed to update folder',
        variant: 'destructive',
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteFolder = async (folderId: string) => {
    if (!confirm('Are you sure you want to delete this folder? Bookmarks will be moved to "All Bookmarks".')) {
      return;
    }

    setDeletingId(folderId);
    try {
      const token = await getIdToken();
      await deleteBookmarkFolder(folderId, token);
      toast({
        title: 'Folder deleted',
        description: 'Folder deleted successfully',
      });
      onFolderCreated();
    } catch (error) {
      console.error('Failed to delete folder:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete folder',
        variant: 'destructive',
      });
    } finally {
      setDeletingId(null);
    }
  };

  const startEdit = (folder: BookmarkFolder) => {
    setEditingFolder(folder);
    setEditName(folder.name);
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Manage Bookmark Folders</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Create new folder */}
          <div className="flex gap-2">
            <Input
              placeholder="New folder name"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleCreateFolder();
                }
              }}
            />
            <Button onClick={handleCreateFolder} disabled={isCreating}>
              {isCreating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
            </Button>
          </div>

          {/* Folder list */}
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {folders.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No folders yet. Create one above.
              </p>
            ) : (
              folders.map((folder) => (
                <div
                  key={folder.id}
                  className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border"
                >
                  {editingFolder?.id === folder.id ? (
                    <div className="flex-1 flex gap-2">
                      <Input
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleUpdateFolder();
                          } else if (e.key === 'Escape') {
                            setEditingFolder(null);
                            setEditName('');
                          }
                        }}
                        autoFocus
                      />
                      <Button
                        size="sm"
                        onClick={handleUpdateFolder}
                        disabled={isUpdating}
                      >
                        {isUpdating ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          'Save'
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setEditingFolder(null);
                          setEditName('');
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <>
                      <div>
                        <p className="font-medium">{folder.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {folder.bookmark_count || 0} bookmarks
                        </p>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => startEdit(folder)}
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeleteFolder(folder.id)}
                          disabled={deletingId === folder.id}
                        >
                          {deletingId === folder.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

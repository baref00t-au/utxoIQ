'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { fetchBookmarks, fetchBookmarkFolders, fetchInsightById } from '@/lib/api';
import { Bookmark, BookmarkFolder, Insight } from '@/types';
import { Button } from '@/components/ui/button';
import { Folder, Plus, Loader2 } from 'lucide-react';
import { InsightCard } from './insight-card';
import { BookmarkFolderManager } from './bookmark-folder-manager';
import { useToast } from '@/hooks/use-toast';

export function BookmarksView() {
  const { user, getIdToken } = useAuth();
  const { toast } = useToast();
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [folders, setFolders] = useState<BookmarkFolder[]>([]);
  const [insights, setInsights] = useState<Record<string, Insight>>({});
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showFolderManager, setShowFolderManager] = useState(false);

  useEffect(() => {
    if (user) {
      loadBookmarksAndFolders();
    }
  }, [user, selectedFolder]);

  const loadBookmarksAndFolders = async () => {
    if (!user) return;

    setIsLoading(true);
    try {
      const token = await getIdToken();
      
      // Load folders
      const foldersData = await fetchBookmarkFolders(token);
      setFolders(foldersData);

      // Load bookmarks
      const bookmarksData = await fetchBookmarks(
        token,
        selectedFolder || undefined
      );
      setBookmarks(bookmarksData);

      // Load insights for bookmarks
      const insightPromises = bookmarksData.map((bookmark: Bookmark) =>
        fetchInsightById(bookmark.insight_id).catch(() => null)
      );
      const insightsData = await Promise.all(insightPromises);
      
      const insightsMap: Record<string, Insight> = {};
      insightsData.forEach((insight) => {
        if (insight) {
          insightsMap[insight.id] = insight;
        }
      });
      setInsights(insightsMap);
    } catch (error) {
      console.error('Failed to load bookmarks:', error);
      toast({
        title: 'Error',
        description: 'Failed to load bookmarks',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFolderCreated = () => {
    loadBookmarksAndFolders();
  };

  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Sign in to view bookmarks</h1>
          <p className="text-muted-foreground">
            Please sign in to access your bookmarked insights
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Bookmarks</h1>
        <Button onClick={() => setShowFolderManager(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Manage Folders
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-card rounded-lg border border-border p-4">
            <h2 className="text-sm font-medium mb-4">Folders</h2>
            
            <button
              onClick={() => setSelectedFolder(null)}
              className={`w-full text-left px-3 py-2 rounded-lg mb-2 transition-colors ${
                selectedFolder === null
                  ? 'bg-brand/10 text-brand'
                  : 'hover:bg-surface'
              }`}
            >
              <div className="flex items-center justify-between">
                <span>All Bookmarks</span>
                <span className="text-xs text-muted-foreground">
                  {bookmarks.length}
                </span>
              </div>
            </button>

            {folders.map((folder) => (
              <button
                key={folder.id}
                onClick={() => setSelectedFolder(folder.id)}
                className={`w-full text-left px-3 py-2 rounded-lg mb-2 transition-colors ${
                  selectedFolder === folder.id
                    ? 'bg-brand/10 text-brand'
                    : 'hover:bg-surface'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Folder className="w-4 h-4" />
                    <span>{folder.name}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {folder.bookmark_count || 0}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-brand" />
            </div>
          ) : bookmarks.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground mb-4">
                {selectedFolder
                  ? 'No bookmarks in this folder'
                  : 'No bookmarks yet'}
              </p>
              <p className="text-sm text-muted-foreground">
                Bookmark insights from the feed to save them here
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {bookmarks.map((bookmark) => {
                const insight = insights[bookmark.insight_id];
                if (!insight) return null;

                return (
                  <div key={bookmark.id}>
                    <InsightCard insight={insight} />
                    {bookmark.note && (
                      <div className="mt-2 p-3 bg-surface rounded-lg border border-border">
                        <p className="text-sm text-muted-foreground">
                          <span className="font-medium">Note:</span> {bookmark.note}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {showFolderManager && (
        <BookmarkFolderManager
          folders={folders}
          onClose={() => setShowFolderManager(false)}
          onFolderCreated={handleFolderCreated}
        />
      )}
    </div>
  );
}

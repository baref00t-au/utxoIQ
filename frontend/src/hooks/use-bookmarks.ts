'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth-context';
import {
  fetchBookmarks,
  fetchBookmarkFolders,
  createBookmark,
  updateBookmark,
  deleteBookmark,
  createBookmarkFolder,
  updateBookmarkFolder,
  deleteBookmarkFolder,
} from '@/lib/api';
import { Bookmark, BookmarkFolder } from '@/types';

interface UseBookmarksOptions {
  folderId?: string;
  autoSync?: boolean;
}

interface PendingOperation {
  id: string;
  type: 'create' | 'update' | 'delete';
  data: any;
  timestamp: number;
}

const STORAGE_KEY = 'utxoiq_bookmarks_cache';
const PENDING_OPS_KEY = 'utxoiq_bookmarks_pending';
const SYNC_INTERVAL = 30000; // 30 seconds

export function useBookmarks(options: UseBookmarksOptions = {}) {
  const { user, getIdToken } = useAuth();
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [folders, setFolders] = useState<BookmarkFolder[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [pendingOperations, setPendingOperations] = useState<PendingOperation[]>([]);

  // Load cached data from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const cached = localStorage.getItem(STORAGE_KEY);
      if (cached) {
        try {
          const data = JSON.parse(cached);
          setBookmarks(data.bookmarks || []);
          setFolders(data.folders || []);
        } catch (error) {
          console.error('Failed to parse cached bookmarks:', error);
        }
      }

      const pending = localStorage.getItem(PENDING_OPS_KEY);
      if (pending) {
        try {
          setPendingOperations(JSON.parse(pending));
        } catch (error) {
          console.error('Failed to parse pending operations:', error);
        }
      }
    }
  }, []);

  // Save to cache whenever data changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ bookmarks, folders, timestamp: Date.now() })
      );
    }
  }, [bookmarks, folders]);

  // Save pending operations to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(PENDING_OPS_KEY, JSON.stringify(pendingOperations));
    }
  }, [pendingOperations]);

  // Sync with server
  const syncWithServer = useCallback(async () => {
    if (!user || isSyncing) return;

    setIsSyncing(true);
    try {
      const token = await getIdToken();

      // Process pending operations first
      if (pendingOperations.length > 0) {
        for (const op of pendingOperations) {
          try {
            switch (op.type) {
              case 'create':
                await createBookmark(op.data, token);
                break;
              case 'update':
                await updateBookmark(op.id, op.data, token);
                break;
              case 'delete':
                await deleteBookmark(op.id, token);
                break;
            }
          } catch (error) {
            console.error('Failed to process pending operation:', error);
            // Keep the operation in the queue if it fails
            continue;
          }
        }
        // Clear processed operations
        setPendingOperations([]);
      }

      // Fetch latest data from server
      const [bookmarksData, foldersData] = await Promise.all([
        fetchBookmarks(token, options.folderId),
        fetchBookmarkFolders(token),
      ]);

      setBookmarks(bookmarksData);
      setFolders(foldersData);
    } catch (error) {
      console.error('Failed to sync bookmarks:', error);
    } finally {
      setIsSyncing(false);
      setIsLoading(false);
    }
  }, [user, isSyncing, pendingOperations, options.folderId]);

  // Initial load and periodic sync
  useEffect(() => {
    if (user) {
      syncWithServer();

      if (options.autoSync !== false) {
        const interval = setInterval(syncWithServer, SYNC_INTERVAL);
        return () => clearInterval(interval);
      }
    }
  }, [user, syncWithServer, options.autoSync]);

  // Optimistic create bookmark
  const addBookmark = useCallback(
    async (insightId: string, folderId?: string, note?: string) => {
      const tempId = `temp_${Date.now()}`;
      const newBookmark: Bookmark = {
        id: tempId,
        user_id: user?.uid || '',
        insight_id: insightId,
        folder_id: folderId,
        note,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      // Optimistic update
      setBookmarks((prev) => [newBookmark, ...prev]);

      // Add to pending operations
      const operation: PendingOperation = {
        id: tempId,
        type: 'create',
        data: { insight_id: insightId, folder_id: folderId, note },
        timestamp: Date.now(),
      };
      setPendingOperations((prev) => [...prev, operation]);

      // Try to sync immediately if online
      if (navigator.onLine) {
        try {
          const token = await getIdToken();
          const result = await createBookmark(
            { insight_id: insightId, folder_id: folderId, note },
            token
          );

          // Replace temp bookmark with real one
          setBookmarks((prev) =>
            prev.map((b) => (b.id === tempId ? result : b))
          );

          // Remove from pending operations
          setPendingOperations((prev) =>
            prev.filter((op) => op.id !== tempId)
          );

          return result;
        } catch (error) {
          console.error('Failed to create bookmark, will retry later:', error);
          throw error;
        }
      }

      return newBookmark;
    },
    [user, getIdToken]
  );

  // Optimistic update bookmark
  const modifyBookmark = useCallback(
    async (bookmarkId: string, data: { folder_id?: string; note?: string }) => {
      // Optimistic update
      setBookmarks((prev) =>
        prev.map((b) =>
          b.id === bookmarkId
            ? { ...b, ...data, updated_at: new Date().toISOString() }
            : b
        )
      );

      // Add to pending operations
      const operation: PendingOperation = {
        id: bookmarkId,
        type: 'update',
        data,
        timestamp: Date.now(),
      };
      setPendingOperations((prev) => [...prev, operation]);

      // Try to sync immediately if online
      if (navigator.onLine) {
        try {
          const token = await getIdToken();
          const result = await updateBookmark(bookmarkId, data, token);

          // Remove from pending operations
          setPendingOperations((prev) =>
            prev.filter((op) => !(op.id === bookmarkId && op.type === 'update'))
          );

          return result;
        } catch (error) {
          console.error('Failed to update bookmark, will retry later:', error);
          throw error;
        }
      }
    },
    [getIdToken]
  );

  // Optimistic delete bookmark
  const removeBookmark = useCallback(
    async (bookmarkId: string) => {
      // Optimistic update
      setBookmarks((prev) => prev.filter((b) => b.id !== bookmarkId));

      // Add to pending operations
      const operation: PendingOperation = {
        id: bookmarkId,
        type: 'delete',
        data: {},
        timestamp: Date.now(),
      };
      setPendingOperations((prev) => [...prev, operation]);

      // Try to sync immediately if online
      if (navigator.onLine) {
        try {
          const token = await getIdToken();
          await deleteBookmark(bookmarkId, token);

          // Remove from pending operations
          setPendingOperations((prev) =>
            prev.filter((op) => !(op.id === bookmarkId && op.type === 'delete'))
          );
        } catch (error) {
          console.error('Failed to delete bookmark, will retry later:', error);
          throw error;
        }
      }
    },
    [getIdToken]
  );

  // Folder operations (similar optimistic pattern)
  const addFolder = useCallback(
    async (name: string) => {
      const tempId = `temp_folder_${Date.now()}`;
      const newFolder: BookmarkFolder = {
        id: tempId,
        user_id: user?.uid || '',
        name,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        bookmark_count: 0,
      };

      setFolders((prev) => [newFolder, ...prev]);

      if (navigator.onLine) {
        try {
          const token = await getIdToken();
          const result = await createBookmarkFolder({ name }, token);
          setFolders((prev) =>
            prev.map((f) => (f.id === tempId ? result : f))
          );
          return result;
        } catch (error) {
          console.error('Failed to create folder:', error);
          throw error;
        }
      }

      return newFolder;
    },
    [user, getIdToken]
  );

  const modifyFolder = useCallback(
    async (folderId: string, name: string) => {
      setFolders((prev) =>
        prev.map((f) =>
          f.id === folderId
            ? { ...f, name, updated_at: new Date().toISOString() }
            : f
        )
      );

      if (navigator.onLine) {
        try {
          const token = await getIdToken();
          const result = await updateBookmarkFolder(folderId, { name }, token);
          return result;
        } catch (error) {
          console.error('Failed to update folder:', error);
          throw error;
        }
      }
    },
    [getIdToken]
  );

  const removeFolder = useCallback(
    async (folderId: string) => {
      setFolders((prev) => prev.filter((f) => f.id !== folderId));

      if (navigator.onLine) {
        try {
          const token = await getIdToken();
          await deleteBookmarkFolder(folderId, token);
        } catch (error) {
          console.error('Failed to delete folder:', error);
          throw error;
        }
      }
    },
    [getIdToken]
  );

  return {
    bookmarks,
    folders,
    isLoading,
    isSyncing,
    hasPendingOperations: pendingOperations.length > 0,
    addBookmark,
    modifyBookmark,
    removeBookmark,
    addFolder,
    modifyFolder,
    removeFolder,
    syncWithServer,
  };
}

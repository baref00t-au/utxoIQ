import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useBookmarks } from '../use-bookmarks';
import * as api from '@/lib/api';
import * as authContext from '@/lib/auth-context';

// Mock the API functions
vi.mock('@/lib/api', () => ({
  fetchBookmarks: vi.fn(),
  fetchBookmarkFolders: vi.fn(),
  createBookmark: vi.fn(),
  updateBookmark: vi.fn(),
  deleteBookmark: vi.fn(),
  createBookmarkFolder: vi.fn(),
  updateBookmarkFolder: vi.fn(),
  deleteBookmarkFolder: vi.fn(),
}));

// Mock the auth context
vi.mock('@/lib/auth-context', () => ({
  useAuth: vi.fn(),
}));

describe('useBookmarks', () => {
  const mockUser = {
    uid: 'user123',
    email: 'test@example.com',
  };

  const mockGetIdToken = vi.fn().mockResolvedValue('mock-token');

  const mockBookmarks = [
    {
      id: 'bookmark1',
      user_id: 'user123',
      insight_id: 'insight1',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'bookmark2',
      user_id: 'user123',
      insight_id: 'insight2',
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    },
  ];

  const mockFolders = [
    {
      id: 'folder1',
      user_id: 'user123',
      name: 'Folder 1',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      bookmark_count: 2,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    
    (authContext.useAuth as any).mockReturnValue({
      user: mockUser,
      getIdToken: mockGetIdToken,
    });

    (api.fetchBookmarks as any).mockResolvedValue(mockBookmarks);
    (api.fetchBookmarkFolders as any).mockResolvedValue(mockFolders);
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it('loads bookmarks and folders on mount', async () => {
    const { result } = renderHook(() => useBookmarks());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.bookmarks).toEqual(mockBookmarks);
    expect(result.current.folders).toEqual(mockFolders);
  });

  it('caches bookmarks in localStorage', async () => {
    const { result } = renderHook(() => useBookmarks());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const cached = localStorage.getItem('utxoiq_bookmarks_cache');
    expect(cached).toBeTruthy();
    
    const data = JSON.parse(cached!);
    expect(data.bookmarks).toEqual(mockBookmarks);
    expect(data.folders).toEqual(mockFolders);
  });

  it('adds bookmark with optimistic update', async () => {
    (api.createBookmark as any).mockResolvedValue({
      id: 'bookmark3',
      user_id: 'user123',
      insight_id: 'insight3',
      created_at: '2024-01-03T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
    });

    const { result } = renderHook(() => useBookmarks());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.addBookmark('insight3');
    });

    // Should immediately add bookmark (optimistic)
    expect(result.current.bookmarks.length).toBe(3);
    expect(result.current.bookmarks[0].insight_id).toBe('insight3');

    await waitFor(() => {
      expect(api.createBookmark).toHaveBeenCalledWith(
        { insight_id: 'insight3', folder_id: undefined, note: undefined },
        'mock-token'
      );
    });
  });

  it('updates bookmark with optimistic update', async () => {
    (api.updateBookmark as any).mockResolvedValue({
      id: 'bookmark1',
      user_id: 'user123',
      insight_id: 'insight1',
      note: 'Updated note',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
    });

    const { result } = renderHook(() => useBookmarks());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.modifyBookmark('bookmark1', { note: 'Updated note' });
    });

    // Should immediately update bookmark (optimistic)
    const updatedBookmark = result.current.bookmarks.find(
      (b) => b.id === 'bookmark1'
    );
    expect(updatedBookmark?.note).toBe('Updated note');

    await waitFor(() => {
      expect(api.updateBookmark).toHaveBeenCalledWith(
        'bookmark1',
        { note: 'Updated note' },
        'mock-token'
      );
    });
  });

  it('deletes bookmark with optimistic update', async () => {
    (api.deleteBookmark as any).mockResolvedValue(undefined);

    const { result } = renderHook(() => useBookmarks());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.removeBookmark('bookmark1');
    });

    // Should immediately remove bookmark (optimistic)
    expect(result.current.bookmarks.length).toBe(1);
    expect(result.current.bookmarks[0].id).toBe('bookmark2');

    await waitFor(() => {
      expect(api.deleteBookmark).toHaveBeenCalledWith(
        'bookmark1',
        'mock-token'
      );
    });
  });

  it('handles offline bookmark creation', async () => {
    // Simulate offline
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    const { result } = renderHook(() => useBookmarks());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.addBookmark('insight3');
    });

    // Should add bookmark optimistically
    expect(result.current.bookmarks.length).toBe(3);
    
    // Should have pending operation
    expect(result.current.hasPendingOperations).toBe(true);

    // API should not be called while offline
    expect(api.createBookmark).not.toHaveBeenCalled();
  });

  it('syncs pending operations when coming online', async () => {
    // Start offline
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    const { result } = renderHook(() => useBookmarks({ autoSync: false }));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.addBookmark('insight3');
    });

    expect(result.current.hasPendingOperations).toBe(true);

    // Go online
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });

    (api.createBookmark as any).mockResolvedValue({
      id: 'bookmark3',
      user_id: 'user123',
      insight_id: 'insight3',
      created_at: '2024-01-03T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
    });

    // Manually trigger sync
    await act(async () => {
      await result.current.syncWithServer();
    });

    await waitFor(() => {
      expect(result.current.hasPendingOperations).toBe(false);
    });

    expect(api.createBookmark).toHaveBeenCalled();
  });

  it('adds folder with optimistic update', async () => {
    (api.createBookmarkFolder as any).mockResolvedValue({
      id: 'folder2',
      user_id: 'user123',
      name: 'New Folder',
      created_at: '2024-01-03T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
      bookmark_count: 0,
    });

    const { result } = renderHook(() => useBookmarks());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.addFolder('New Folder');
    });

    // Should immediately add folder (optimistic)
    expect(result.current.folders.length).toBe(2);
    expect(result.current.folders[0].name).toBe('New Folder');

    await waitFor(() => {
      expect(api.createBookmarkFolder).toHaveBeenCalledWith(
        { name: 'New Folder' },
        'mock-token'
      );
    });
  });
});

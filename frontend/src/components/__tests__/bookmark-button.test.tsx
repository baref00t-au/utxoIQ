import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BookmarkButton } from '../insights/bookmark-button';
import * as api from '@/lib/api';
import * as authContext from '@/lib/auth-context';

// Mock the API functions
vi.mock('@/lib/api', () => ({
  checkBookmark: vi.fn(),
  createBookmark: vi.fn(),
  deleteBookmark: vi.fn(),
}));

// Mock the auth context
vi.mock('@/lib/auth-context', () => ({
  useAuth: vi.fn(),
}));

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe('BookmarkButton', () => {
  const mockUser = {
    uid: 'user123',
    email: 'test@example.com',
  };

  const mockGetIdToken = vi.fn().mockResolvedValue('mock-token');

  beforeEach(() => {
    vi.clearAllMocks();
    (authContext.useAuth as any).mockReturnValue({
      user: mockUser,
      getIdToken: mockGetIdToken,
    });
  });

  it('renders bookmark button', () => {
    (api.checkBookmark as any).mockResolvedValue({ exists: false });
    
    render(<BookmarkButton insightId="insight123" />);
    
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('shows bookmarked state when bookmark exists', async () => {
    (api.checkBookmark as any).mockResolvedValue({
      exists: true,
      bookmark_id: 'bookmark123',
    });
    
    render(<BookmarkButton insightId="insight123" />);
    
    await waitFor(() => {
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Remove bookmark');
    });
  });

  it('creates bookmark when clicked and not bookmarked', async () => {
    (api.checkBookmark as any).mockResolvedValue({ exists: false });
    (api.createBookmark as any).mockResolvedValue({
      id: 'bookmark123',
      insight_id: 'insight123',
    });
    
    render(<BookmarkButton insightId="insight123" />);
    
    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(api.createBookmark).toHaveBeenCalledWith(
        { insight_id: 'insight123' },
        'mock-token'
      );
    });
  });

  it('deletes bookmark when clicked and bookmarked', async () => {
    (api.checkBookmark as any).mockResolvedValue({
      exists: true,
      bookmark_id: 'bookmark123',
    });
    (api.deleteBookmark as any).mockResolvedValue(undefined);
    
    render(<BookmarkButton insightId="insight123" />);
    
    await waitFor(() => {
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Remove bookmark');
    });
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(api.deleteBookmark).toHaveBeenCalledWith(
        'bookmark123',
        'mock-token'
      );
    });
  });

  it('shows sign in message when user is not authenticated', async () => {
    (authContext.useAuth as any).mockReturnValue({
      user: null,
      getIdToken: mockGetIdToken,
    });
    
    const { toast } = require('@/hooks/use-toast').useToast();
    
    render(<BookmarkButton insightId="insight123" />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(toast).toHaveBeenCalled();
    });
  });

  it('disables button while loading', async () => {
    (api.checkBookmark as any).mockResolvedValue({ exists: false });
    (api.createBookmark as any).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );
    
    render(<BookmarkButton insightId="insight123" />);
    
    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(button).toBeDisabled();
  });
});

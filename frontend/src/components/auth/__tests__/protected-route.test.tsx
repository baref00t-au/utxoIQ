import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ProtectedRoute } from '../protected-route';
import * as authContext from '@/lib/auth-context';

// Mock next/navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state while checking auth', () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: null,
      firebaseUser: null,
      loading: true,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
      signInWithGithub: vi.fn(),
      signOut: vi.fn(),
      resetPassword: vi.fn(),
      refreshProfile: vi.fn(),
    });

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('redirects to sign-in when user is not authenticated', async () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: null,
      firebaseUser: null,
      loading: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
      signInWithGithub: vi.fn(),
      signOut: vi.fn(),
      resetPassword: vi.fn(),
      refreshProfile: vi.fn(),
    });

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/sign-in');
    });
  });

  it('renders children when user is authenticated', () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: {
        id: '1',
        email: 'test@example.com',
        role: 'user',
        subscriptionTier: 'free',
      },
      firebaseUser: null,
      loading: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
      signInWithGithub: vi.fn(),
      signOut: vi.fn(),
      resetPassword: vi.fn(),
      refreshProfile: vi.fn(),
    });

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects to pricing when subscription tier is insufficient', async () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: {
        id: '1',
        email: 'test@example.com',
        role: 'user',
        subscriptionTier: 'free',
      },
      firebaseUser: null,
      loading: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
      signInWithGithub: vi.fn(),
      signOut: vi.fn(),
      resetPassword: vi.fn(),
      refreshProfile: vi.fn(),
    });

    render(
      <ProtectedRoute requireTier="pro">
        <div>Pro Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/pricing');
    });
  });

  it('renders children when subscription tier is sufficient', () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: {
        id: '1',
        email: 'test@example.com',
        role: 'user',
        subscriptionTier: 'pro',
      },
      firebaseUser: null,
      loading: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
      signInWithGithub: vi.fn(),
      signOut: vi.fn(),
      resetPassword: vi.fn(),
      refreshProfile: vi.fn(),
    });

    render(
      <ProtectedRoute requireTier="pro">
        <div>Pro Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Pro Content')).toBeInTheDocument();
  });
});

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SignInForm } from '../sign-in-form';
import * as authContext from '@/lib/auth-context';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

// Mock sonner
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('SignInForm', () => {
  const mockSignIn = vi.fn();
  const mockSignInWithGoogle = vi.fn();
  const mockSignInWithGithub = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: null,
      firebaseUser: null,
      loading: false,
      signIn: mockSignIn,
      signUp: vi.fn(),
      signInWithGoogle: mockSignInWithGoogle,
      signInWithGithub: mockSignInWithGithub,
      signOut: vi.fn(),
      resetPassword: vi.fn(),
      refreshProfile: vi.fn(),
    });
  });

  it('renders sign in form', () => {
    render(<SignInForm />);
    
    expect(screen.getByText('Sign in to utxoIQ')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('handles email/password sign in', async () => {
    mockSignIn.mockResolvedValue(undefined);
    render(<SignInForm />);

    const emailInput = screen.getByLabelText('Email');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith('test@example.com', 'password123');
    });
  });

  it('handles Google sign in', async () => {
    mockSignInWithGoogle.mockResolvedValue(undefined);
    render(<SignInForm />);

    const googleButton = screen.getByRole('button', { name: /google/i });
    fireEvent.click(googleButton);

    await waitFor(() => {
      expect(mockSignInWithGoogle).toHaveBeenCalled();
    });
  });

  it('handles GitHub sign in', async () => {
    mockSignInWithGithub.mockResolvedValue(undefined);
    render(<SignInForm />);

    const githubButton = screen.getByRole('button', { name: /github/i });
    fireEvent.click(githubButton);

    await waitFor(() => {
      expect(mockSignInWithGithub).toHaveBeenCalled();
    });
  });

  it('displays error on failed sign in', async () => {
    mockSignIn.mockRejectedValue(new Error('Invalid credentials'));
    render(<SignInForm />);

    const emailInput = screen.getByLabelText('Email');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalled();
    });
  });
});

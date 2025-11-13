'use client';

import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireTier?: 'pro' | 'power';
}

export function ProtectedRoute({ children, requireTier }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/sign-in');
    }

    if (!loading && user && requireTier) {
      const tierHierarchy: Record<string, number> = {
        free: 0,
        pro: 1,
        power: 2,
      };
      const userLevel = tierHierarchy[user.subscriptionTier] || 0;
      const requiredLevel = tierHierarchy[requireTier] || 0;

      if (userLevel < requiredLevel) {
        router.push('/pricing');
      }
    }
  }, [user, loading, requireTier, router]);

  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-128px)] items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-orange-500" />
          <p className="mt-4 text-sm text-zinc-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (requireTier) {
    const tierHierarchy: Record<string, number> = {
      free: 0,
      pro: 1,
      power: 2,
    };
    const userLevel = tierHierarchy[user.subscriptionTier] || 0;
    const requiredLevel = tierHierarchy[requireTier] || 0;

    if (userLevel < requiredLevel) {
      return null;
    }
  }

  return <>{children}</>;
}

'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Loader2, User, Mail, Shield, Crown } from 'lucide-react';

export function ProfileSettings() {
  const { user, firebaseUser, refreshProfile } = useAuth();
  const [displayName, setDisplayName] = useState(user?.displayName || '');
  const [loading, setLoading] = useState(false);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const idToken = await firebaseUser?.getIdToken();
      const response = await fetch('/api/v1/auth/profile', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({ displayName }),
      });

      if (!response.ok) {
        throw new Error('Failed to update profile');
      }

      await refreshProfile();
      toast.success('Profile updated successfully');
    } catch (error: any) {
      console.error('Update profile error:', error);
      toast.error(error.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="mx-auto max-w-2xl space-y-8">
        <div>
          <h1 className="text-3xl font-semibold text-zinc-50">Profile Settings</h1>
          <p className="mt-2 text-sm text-zinc-400">
            Manage your account information and preferences
          </p>
        </div>

        <div className="space-y-6">
          {/* Account Information */}
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
            <h2 className="mb-4 text-lg font-semibold text-zinc-50">
              Account Information
            </h2>
            <div className="space-y-4">
              <div className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                <Mail className="h-5 w-5 text-zinc-400" />
                <div>
                  <p className="text-sm font-medium text-zinc-300">Email</p>
                  <p className="text-sm text-zinc-400">{user?.email}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                <Shield className="h-5 w-5 text-zinc-400" />
                <div>
                  <p className="text-sm font-medium text-zinc-300">Role</p>
                  <p className="text-sm text-zinc-400">{user?.role}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                <Crown className="h-5 w-5 text-orange-500" />
                <div>
                  <p className="text-sm font-medium text-zinc-300">Subscription Tier</p>
                  <p className="text-sm capitalize text-orange-500">
                    {user?.subscriptionTier}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Display Name */}
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
            <h2 className="mb-4 text-lg font-semibold text-zinc-50">Display Name</h2>
            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="displayName">Display Name</Label>
                <Input
                  id="displayName"
                  type="text"
                  placeholder="Enter your display name"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  disabled={loading}
                />
                <p className="text-xs text-zinc-500">
                  This is how your name will appear across the platform
                </p>
              </div>

              <Button type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Save Changes'
                )}
              </Button>
            </form>
          </div>

          {/* Email Verification Status */}
          {firebaseUser && !firebaseUser.emailVerified && (
            <div className="rounded-2xl border border-orange-500/20 bg-orange-500/10 p-6">
              <h2 className="mb-2 text-lg font-semibold text-orange-500">
                Email Not Verified
              </h2>
              <p className="text-sm text-zinc-400">
                Please check your email and click the verification link to verify your
                account.
              </p>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}

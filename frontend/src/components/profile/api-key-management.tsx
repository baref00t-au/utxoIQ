'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Loader2, Key, Trash2, Copy, Plus, AlertCircle } from 'lucide-react';

interface APIKey {
  id: string;
  keyPrefix: string;
  name: string;
  scopes: string[];
  createdAt: string;
  lastUsedAt?: string;
}

export function APIKeyManagement() {
  const { firebaseUser } = useAuth();
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeySecret, setNewKeySecret] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    fetchAPIKeys();
  }, []);

  const fetchAPIKeys = async () => {
    try {
      const idToken = await firebaseUser?.getIdToken();
      const response = await fetch('/api/v1/auth/api-keys', {
        headers: { Authorization: `Bearer ${idToken}` },
      });

      if (response.ok) {
        const keys = await response.json();
        setApiKeys(keys);
      }
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);

    try {
      const idToken = await firebaseUser?.getIdToken();
      const response = await fetch('/api/v1/auth/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          name: newKeyName,
          scopes: ['insights:read', 'alerts:read', 'alerts:write'],
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create API key');
      }

      const newKey = await response.json();
      setNewKeySecret(newKey.key);
      setApiKeys([...apiKeys, newKey]);
      setNewKeyName('');
      toast.success('API key created successfully');
    } catch (error: any) {
      console.error('Create API key error:', error);
      toast.error(error.message || 'Failed to create API key');
    } finally {
      setCreating(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
      return;
    }

    try {
      const idToken = await firebaseUser?.getIdToken();
      const response = await fetch(`/api/v1/auth/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${idToken}` },
      });

      if (!response.ok) {
        throw new Error('Failed to revoke API key');
      }

      setApiKeys(apiKeys.filter((key) => key.id !== keyId));
      toast.success('API key revoked successfully');
    } catch (error: any) {
      console.error('Revoke API key error:', error);
      toast.error(error.message || 'Failed to revoke API key');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  return (
    <ProtectedRoute>
      <div className="mx-auto max-w-4xl space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-zinc-50">API Keys</h1>
            <p className="mt-2 text-sm text-zinc-400">
              Manage your API keys for programmatic access
            </p>
          </div>
          {!showCreateForm && apiKeys.length < 5 && (
            <Button onClick={() => setShowCreateForm(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create API Key
            </Button>
          )}
        </div>

        {/* New Key Secret Display */}
        {newKeySecret && (
          <div className="rounded-2xl border border-green-500/20 bg-green-500/10 p-6">
            <div className="mb-4 flex items-start gap-3">
              <AlertCircle className="mt-0.5 h-5 w-5 text-green-500" />
              <div>
                <h3 className="font-semibold text-green-500">API Key Created</h3>
                <p className="mt-1 text-sm text-zinc-400">
                  Make sure to copy your API key now. You won't be able to see it again!
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Input
                value={newKeySecret}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(newKeySecret)}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => setNewKeySecret(null)}
            >
              Done
            </Button>
          </div>
        )}

        {/* Create Form */}
        {showCreateForm && (
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
            <h2 className="mb-4 text-lg font-semibold text-zinc-50">Create New API Key</h2>
            <form onSubmit={handleCreateKey} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="keyName">Key Name</Label>
                <Input
                  id="keyName"
                  type="text"
                  placeholder="My API Key"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  required
                  disabled={creating}
                />
                <p className="text-xs text-zinc-500">
                  A descriptive name to help you identify this key
                </p>
              </div>

              <div className="flex gap-2">
                <Button type="submit" disabled={creating}>
                  {creating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Key'
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewKeyName('');
                  }}
                  disabled={creating}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* API Keys List */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
          <h2 className="mb-4 text-lg font-semibold text-zinc-50">Your API Keys</h2>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
            </div>
          ) : apiKeys.length === 0 ? (
            <div className="py-8 text-center">
              <Key className="mx-auto h-12 w-12 text-zinc-600" />
              <p className="mt-4 text-sm text-zinc-400">No API keys yet</p>
              <p className="mt-1 text-xs text-zinc-500">
                Create your first API key to get started
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950 p-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Key className="h-4 w-4 text-zinc-400" />
                      <p className="font-medium text-zinc-300">{key.name}</p>
                    </div>
                    <p className="mt-1 font-mono text-xs text-zinc-500">
                      {key.keyPrefix}••••••••••••••••
                    </p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-zinc-500">
                      <span>Created {new Date(key.createdAt).toLocaleDateString()}</span>
                      {key.lastUsedAt && (
                        <span>
                          Last used {new Date(key.lastUsedAt).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRevokeKey(key.id)}
                    className="text-red-500 hover:bg-red-500/10 hover:text-red-400"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
          {apiKeys.length >= 5 && (
            <p className="mt-4 text-xs text-zinc-500">
              You've reached the maximum of 5 API keys. Revoke an existing key to create a
              new one.
            </p>
          )}
        </div>

        {/* Rate Limit Info */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
          <h2 className="mb-4 text-lg font-semibold text-zinc-50">Rate Limits</h2>
          <div className="space-y-2 text-sm text-zinc-400">
            <p>API keys are subject to the same rate limits as your subscription tier:</p>
            <ul className="ml-6 list-disc space-y-1">
              <li>Free: 100 requests per hour</li>
              <li>Pro: 1,000 requests per hour</li>
              <li>Power: 10,000 requests per hour</li>
            </ul>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

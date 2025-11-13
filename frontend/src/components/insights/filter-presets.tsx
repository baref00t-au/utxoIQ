'use client';

import { useState, useEffect } from 'react';
import { FilterState, FilterPreset } from '@/types';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Save, Trash2, Edit2, Check, X } from 'lucide-react';
import {
  fetchFilterPresets,
  createFilterPreset,
  updateFilterPreset,
  deleteFilterPreset,
} from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface FilterPresetsProps {
  currentFilters: FilterState;
  onApplyPreset: (filters: FilterState) => void;
  authToken?: string;
}

export function FilterPresets({
  currentFilters,
  onApplyPreset,
  authToken,
}: FilterPresetsProps) {
  const [presets, setPresets] = useState<FilterPreset[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaveDialogOpen, setIsSaveDialogOpen] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const { toast } = useToast();

  // Load presets on mount
  useEffect(() => {
    if (authToken) {
      loadPresets();
    }
  }, [authToken]);

  const loadPresets = async () => {
    if (!authToken) return;

    try {
      setIsLoading(true);
      const response = await fetchFilterPresets(authToken);
      setPresets(response.presets || []);
    } catch (error) {
      console.error('Failed to load filter presets:', error);
      toast({
        title: 'Error',
        description: 'Failed to load filter presets',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSavePreset = async () => {
    if (!authToken || !presetName.trim()) return;

    try {
      setIsLoading(true);
      const newPreset = await createFilterPreset(
        {
          name: presetName.trim(),
          filters: currentFilters,
        },
        authToken
      );

      setPresets([...presets, newPreset]);
      setPresetName('');
      setIsSaveDialogOpen(false);

      toast({
        title: 'Success',
        description: 'Filter preset saved successfully',
      });
    } catch (error: any) {
      console.error('Failed to save filter preset:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to save filter preset',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyPreset = (preset: FilterPreset) => {
    onApplyPreset(preset.filters);
    toast({
      title: 'Preset Applied',
      description: `Applied "${preset.name}" filter preset`,
    });
  };

  const handleStartEdit = (preset: FilterPreset) => {
    setEditingId(preset.id);
    setEditingName(preset.name);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingName('');
  };

  const handleSaveEdit = async (presetId: string) => {
    if (!authToken || !editingName.trim()) return;

    try {
      setIsLoading(true);
      const updatedPreset = await updateFilterPreset(
        presetId,
        { name: editingName.trim() },
        authToken
      );

      setPresets(
        presets.map((p) => (p.id === presetId ? updatedPreset : p))
      );
      setEditingId(null);
      setEditingName('');

      toast({
        title: 'Success',
        description: 'Filter preset updated successfully',
      });
    } catch (error) {
      console.error('Failed to update filter preset:', error);
      toast({
        title: 'Error',
        description: 'Failed to update filter preset',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeletePreset = async (presetId: string) => {
    if (!authToken) return;

    if (!confirm('Are you sure you want to delete this preset?')) {
      return;
    }

    try {
      setIsLoading(true);
      await deleteFilterPreset(presetId, authToken);
      setPresets(presets.filter((p) => p.id !== presetId));

      toast({
        title: 'Success',
        description: 'Filter preset deleted successfully',
      });
    } catch (error) {
      console.error('Failed to delete filter preset:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete filter preset',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!authToken) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6">
        <p className="text-sm text-muted-foreground">
          Sign in to save and manage filter presets
        </p>
      </div>
    );
  }

  const canSaveMore = presets.length < 10;

  return (
    <div className="space-y-4 rounded-2xl border border-border bg-card p-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Saved Filters</h3>
        <Dialog open={isSaveDialogOpen} onOpenChange={setIsSaveDialogOpen}>
          <DialogTrigger asChild>
            <Button
              size="sm"
              variant="outline"
              disabled={!canSaveMore || isLoading}
            >
              <Save className="h-4 w-4 mr-2" />
              Save Current
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Save Filter Preset</DialogTitle>
              <DialogDescription>
                Give your filter preset a name to save it for quick access later.
                {!canSaveMore && (
                  <span className="block mt-2 text-destructive">
                    Maximum of 10 presets reached. Delete a preset to save a new one.
                  </span>
                )}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="preset-name">Preset Name</Label>
                <Input
                  id="preset-name"
                  placeholder="e.g., High Confidence Mempool"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  maxLength={100}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsSaveDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSavePreset}
                disabled={!presetName.trim() || isLoading}
              >
                Save Preset
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {presets.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No saved presets yet. Save your current filters to quickly apply them later.
        </p>
      ) : (
        <div className="space-y-2">
          {presets.map((preset) => (
            <div
              key={preset.id}
              className="flex items-center gap-2 rounded-lg border border-border p-3 hover:bg-accent/50 transition-colors"
            >
              {editingId === preset.id ? (
                <>
                  <Input
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    className="flex-1"
                    maxLength={100}
                  />
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => handleSaveEdit(preset.id)}
                    disabled={!editingName.trim() || isLoading}
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={handleCancelEdit}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => handleApplyPreset(preset)}
                    className="flex-1 text-left text-sm font-medium hover:text-brand transition-colors"
                    disabled={isLoading}
                  >
                    {preset.name}
                  </button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => handleStartEdit(preset)}
                    disabled={isLoading}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => handleDeletePreset(preset.id)}
                    disabled={isLoading}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {presets.length > 0 && (
        <p className="text-xs text-muted-foreground">
          {presets.length} of 10 presets used
        </p>
      )}
    </div>
  );
}

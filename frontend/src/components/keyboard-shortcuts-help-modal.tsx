'use client';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { KeyboardShortcut } from '@/hooks/use-keyboard-shortcuts';
import { Keyboard } from 'lucide-react';

interface KeyboardShortcutsHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
  shortcuts: KeyboardShortcut[];
}

export function KeyboardShortcutsHelpModal({
  isOpen,
  onClose,
  shortcuts,
}: KeyboardShortcutsHelpModalProps) {
  // Group shortcuts by category
  const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
    const category = shortcut.category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(shortcut);
    return acc;
  }, {} as Record<string, KeyboardShortcut[]>);

  const categories = Object.keys(groupedShortcuts).sort();

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Keyboard className="h-5 w-5 text-brand" />
            <DialogTitle>Keyboard Shortcuts</DialogTitle>
          </div>
          <DialogDescription>
            Use these keyboard shortcuts to navigate and interact more efficiently
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {categories.map((category) => (
            <div key={category}>
              <h3 className="text-sm font-semibold text-foreground mb-3">
                {category}
              </h3>
              <div className="space-y-2">
                {groupedShortcuts[category].map((shortcut, index) => (
                  <div
                    key={`${category}-${index}`}
                    className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <span className="text-sm text-muted-foreground">
                      {shortcut.description}
                    </span>
                    <div className="flex items-center gap-1">
                      <ShortcutKeys shortcut={shortcut} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-4 border-t border-border">
          <p className="text-xs text-muted-foreground text-center">
            Press <kbd className="kbd">Esc</kbd> to close this dialog
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

interface ShortcutKeysProps {
  shortcut: KeyboardShortcut;
}

function ShortcutKeys({ shortcut }: ShortcutKeysProps) {
  const keys: string[] = [];

  if (shortcut.ctrl) {
    keys.push(isMac() ? '⌘' : 'Ctrl');
  }
  if (shortcut.shift) {
    keys.push('⇧');
  }
  if (shortcut.alt) {
    keys.push(isMac() ? '⌥' : 'Alt');
  }

  // Format the main key
  let mainKey = shortcut.key;
  if (mainKey === ' ') {
    mainKey = 'Space';
  } else if (mainKey === 'Escape') {
    mainKey = 'Esc';
  } else if (mainKey === 'ArrowUp') {
    mainKey = '↑';
  } else if (mainKey === 'ArrowDown') {
    mainKey = '↓';
  } else if (mainKey === 'ArrowLeft') {
    mainKey = '←';
  } else if (mainKey === 'ArrowRight') {
    mainKey = '→';
  }

  keys.push(mainKey);

  return (
    <>
      {keys.map((key, index) => (
        <span key={index} className="flex items-center">
          <kbd className="kbd">{key}</kbd>
          {index < keys.length - 1 && (
            <span className="mx-1 text-muted-foreground">+</span>
          )}
        </span>
      ))}
    </>
  );
}

function isMac(): boolean {
  if (typeof window === 'undefined') return false;
  return /Mac|iPhone|iPad|iPod/.test(navigator.platform);
}

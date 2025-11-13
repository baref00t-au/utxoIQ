'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { KeyboardShortcut, useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { KeyboardShortcutsHelpModal } from '@/components/keyboard-shortcuts-help-modal';

interface KeyboardShortcutsContextType {
  registerShortcuts: (shortcuts: KeyboardShortcut[]) => void;
  unregisterShortcuts: (shortcuts: KeyboardShortcut[]) => void;
  getAllShortcuts: () => KeyboardShortcut[];
  showHelp: () => void;
  hideHelp: () => void;
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextType | undefined>(
  undefined
);

export function useKeyboardShortcutsContext() {
  const context = useContext(KeyboardShortcutsContext);
  if (!context) {
    throw new Error(
      'useKeyboardShortcutsContext must be used within KeyboardShortcutsProvider'
    );
  }
  return context;
}

interface KeyboardShortcutsProviderProps {
  children: ReactNode;
}

export function KeyboardShortcutsProvider({ children }: KeyboardShortcutsProviderProps) {
  const [shortcuts, setShortcuts] = useState<KeyboardShortcut[]>([]);
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  const registerShortcuts = useCallback((newShortcuts: KeyboardShortcut[]) => {
    setShortcuts((prev) => [...prev, ...newShortcuts]);
  }, []);

  const unregisterShortcuts = useCallback((shortcutsToRemove: KeyboardShortcut[]) => {
    setShortcuts((prev) =>
      prev.filter((s) => !shortcutsToRemove.some((r) => r.key === s.key))
    );
  }, []);

  const getAllShortcuts = useCallback(() => shortcuts, [shortcuts]);

  const showHelp = useCallback(() => setIsHelpOpen(true), []);
  const hideHelp = useCallback(() => setIsHelpOpen(false), []);

  // Global shortcuts that are always active
  const globalShortcuts: KeyboardShortcut[] = [
    {
      key: '?',
      shift: true,
      action: showHelp,
      description: 'Show keyboard shortcuts',
      category: 'General',
    },
    {
      key: 'Escape',
      action: hideHelp,
      description: 'Close modals and dialogs',
      category: 'General',
    },
  ];

  useKeyboardShortcuts(globalShortcuts);

  return (
    <KeyboardShortcutsContext.Provider
      value={{
        registerShortcuts,
        unregisterShortcuts,
        getAllShortcuts,
        showHelp,
        hideHelp,
      }}
    >
      {children}
      <KeyboardShortcutsHelpModal
        isOpen={isHelpOpen}
        onClose={hideHelp}
        shortcuts={[...globalShortcuts, ...shortcuts]}
      />
    </KeyboardShortcutsContext.Provider>
  );
}

import { useEffect, useRef } from 'react';
import { KeyboardShortcut, useKeyboardShortcuts } from './use-keyboard-shortcuts';

interface UseInsightFeedShortcutsOptions {
  onFocusSearch?: () => void;
  onNavigateUp?: () => void;
  onNavigateDown?: () => void;
  enabled?: boolean;
}

/**
 * Hook to add keyboard shortcuts for the insight feed
 */
export function useInsightFeedShortcuts(options: UseInsightFeedShortcutsOptions = {}) {
  const { onFocusSearch, onNavigateUp, onNavigateDown, enabled = true } = options;
  const currentIndexRef = useRef<number>(-1);

  const shortcuts: KeyboardShortcut[] = [];

  // "/" to focus search
  if (onFocusSearch) {
    shortcuts.push({
      key: '/',
      action: onFocusSearch,
      description: 'Focus search input',
      category: 'Navigation',
    });
  }

  // Arrow key navigation
  if (onNavigateUp) {
    shortcuts.push({
      key: 'ArrowUp',
      action: onNavigateUp,
      description: 'Navigate to previous insight',
      category: 'Navigation',
    });
  }

  if (onNavigateDown) {
    shortcuts.push({
      key: 'ArrowDown',
      action: onNavigateDown,
      description: 'Navigate to next insight',
      category: 'Navigation',
    });
  }

  useKeyboardShortcuts(shortcuts, { enabled });

  return {
    currentIndex: currentIndexRef.current,
    setCurrentIndex: (index: number) => {
      currentIndexRef.current = index;
    },
  };
}

/**
 * Hook to add keyboard shortcuts for list navigation
 */
export function useListNavigation(itemCount: number, onSelect?: (index: number) => void) {
  const currentIndexRef = useRef<number>(-1);

  const navigateUp = () => {
    if (currentIndexRef.current > 0) {
      currentIndexRef.current -= 1;
      focusItem(currentIndexRef.current);
      onSelect?.(currentIndexRef.current);
    }
  };

  const navigateDown = () => {
    if (currentIndexRef.current < itemCount - 1) {
      currentIndexRef.current += 1;
      focusItem(currentIndexRef.current);
      onSelect?.(currentIndexRef.current);
    }
  };

  const focusItem = (index: number) => {
    const items = document.querySelectorAll('[data-insight-card]');
    const item = items[index] as HTMLElement;
    if (item) {
      item.focus();
      item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };

  const shortcuts: KeyboardShortcut[] = [
    {
      key: 'ArrowUp',
      action: navigateUp,
      description: 'Navigate to previous item',
      category: 'Navigation',
    },
    {
      key: 'ArrowDown',
      action: navigateDown,
      description: 'Navigate to next item',
      category: 'Navigation',
    },
  ];

  useKeyboardShortcuts(shortcuts);

  return {
    currentIndex: currentIndexRef.current,
    setCurrentIndex: (index: number) => {
      currentIndexRef.current = index;
    },
  };
}

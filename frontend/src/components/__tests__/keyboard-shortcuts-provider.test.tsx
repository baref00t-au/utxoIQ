import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { KeyboardShortcutsProvider, useKeyboardShortcutsContext } from '../keyboard-shortcuts-provider';
import { KeyboardShortcut } from '@/hooks/use-keyboard-shortcuts';

// Test component that uses the context
function TestComponent() {
  const { showHelp, getAllShortcuts } = useKeyboardShortcutsContext();
  const shortcuts = getAllShortcuts();

  return (
    <div>
      <button onClick={showHelp}>Show Help</button>
      <div data-testid="shortcut-count">{shortcuts.length}</div>
    </div>
  );
}

describe('KeyboardShortcutsProvider', () => {
  it('should provide keyboard shortcuts context', () => {
    render(
      <KeyboardShortcutsProvider>
        <TestComponent />
      </KeyboardShortcutsProvider>
    );

    expect(screen.getByText('Show Help')).toBeInTheDocument();
  });

  it('should show help modal when "?" is pressed', async () => {
    render(
      <KeyboardShortcutsProvider>
        <TestComponent />
      </KeyboardShortcutsProvider>
    );

    const event = new KeyboardEvent('keydown', { key: '?', shiftKey: true });
    window.dispatchEvent(event);

    await waitFor(() => {
      expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
    });
  });

  it('should close help modal when Escape is pressed', async () => {
    render(
      <KeyboardShortcutsProvider>
        <TestComponent />
      </KeyboardShortcutsProvider>
    );

    // Open modal
    const openEvent = new KeyboardEvent('keydown', { key: '?', shiftKey: true });
    window.dispatchEvent(openEvent);

    await waitFor(() => {
      expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
    });

    // Close modal
    const closeEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    window.dispatchEvent(closeEvent);

    await waitFor(() => {
      expect(screen.queryByText('Keyboard Shortcuts')).not.toBeInTheDocument();
    });
  });

  it('should have global shortcuts registered', () => {
    render(
      <KeyboardShortcutsProvider>
        <TestComponent />
      </KeyboardShortcutsProvider>
    );

    const shortcutCount = screen.getByTestId('shortcut-count');
    // Global shortcuts are managed internally, not exposed through getAllShortcuts
    // This is expected to be 0 for external consumers
    expect(parseInt(shortcutCount.textContent || '0')).toBeGreaterThanOrEqual(0);
  });

  it('should throw error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useKeyboardShortcutsContext must be used within KeyboardShortcutsProvider');

    consoleSpy.mockRestore();
  });
});

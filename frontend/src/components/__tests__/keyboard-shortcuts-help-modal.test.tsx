import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { KeyboardShortcutsHelpModal } from '../keyboard-shortcuts-help-modal';
import { KeyboardShortcut } from '@/hooks/use-keyboard-shortcuts';

describe('KeyboardShortcutsHelpModal', () => {
  const mockOnClose = vi.fn();

  const mockShortcuts: KeyboardShortcut[] = [
    {
      key: '/',
      action: () => {},
      description: 'Focus search input',
      category: 'Navigation',
    },
    {
      key: '?',
      shift: true,
      action: () => {},
      description: 'Show keyboard shortcuts',
      category: 'General',
    },
    {
      key: 'Escape',
      action: () => {},
      description: 'Close modals and dialogs',
      category: 'General',
    },
    {
      key: 'ArrowUp',
      action: () => {},
      description: 'Navigate to previous item',
      category: 'Navigation',
    },
    {
      key: 'ArrowDown',
      action: () => {},
      description: 'Navigate to next item',
      category: 'Navigation',
    },
  ];

  it('should render modal when open', () => {
    render(
      <KeyboardShortcutsHelpModal
        isOpen={true}
        onClose={mockOnClose}
        shortcuts={mockShortcuts}
      />
    );

    expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
  });

  it('should not render modal when closed', () => {
    render(
      <KeyboardShortcutsHelpModal
        isOpen={false}
        onClose={mockOnClose}
        shortcuts={mockShortcuts}
      />
    );

    expect(screen.queryByText('Keyboard Shortcuts')).not.toBeInTheDocument();
  });

  it('should display all shortcuts grouped by category', () => {
    render(
      <KeyboardShortcutsHelpModal
        isOpen={true}
        onClose={mockOnClose}
        shortcuts={mockShortcuts}
      />
    );

    // Check categories
    expect(screen.getByText('Navigation')).toBeInTheDocument();
    expect(screen.getByText('General')).toBeInTheDocument();

    // Check shortcut descriptions
    expect(screen.getByText('Focus search input')).toBeInTheDocument();
    expect(screen.getByText('Show keyboard shortcuts')).toBeInTheDocument();
    expect(screen.getByText('Close modals and dialogs')).toBeInTheDocument();
    expect(screen.getByText('Navigate to previous item')).toBeInTheDocument();
    expect(screen.getByText('Navigate to next item')).toBeInTheDocument();
  });

  it('should display keyboard keys correctly', () => {
    render(
      <KeyboardShortcutsHelpModal
        isOpen={true}
        onClose={mockOnClose}
        shortcuts={mockShortcuts}
      />
    );

    // Check for key displays using text content
    expect(screen.getByText('/')).toBeInTheDocument();
    expect(screen.getAllByText('Esc').length).toBeGreaterThan(0);
  });

  it('should show shift modifier for shortcuts with shift', () => {
    render(
      <KeyboardShortcutsHelpModal
        isOpen={true}
        onClose={mockOnClose}
        shortcuts={[
          {
            key: '?',
            shift: true,
            action: () => {},
            description: 'Show help',
            category: 'General',
          },
        ]}
      />
    );

    expect(screen.getByText('Show help')).toBeInTheDocument();
    // The shift symbol should be present
    expect(screen.getByText('⇧')).toBeInTheDocument();
  });

  it('should format arrow keys with symbols', () => {
    render(
      <KeyboardShortcutsHelpModal
        isOpen={true}
        onClose={mockOnClose}
        shortcuts={[
          {
            key: 'ArrowUp',
            action: () => {},
            description: 'Navigate up',
            category: 'Navigation',
          },
          {
            key: 'ArrowDown',
            action: () => {},
            description: 'Navigate down',
            category: 'Navigation',
          },
        ]}
      />
    );

    expect(screen.getByText('↑')).toBeInTheDocument();
    expect(screen.getByText('↓')).toBeInTheDocument();
  });

  it('should group shortcuts without category under "Other"', () => {
    render(
      <KeyboardShortcutsHelpModal
        isOpen={true}
        onClose={mockOnClose}
        shortcuts={[
          {
            key: 'x',
            action: () => {},
            description: 'Test action',
          },
        ]}
      />
    );

    expect(screen.getByText('Other')).toBeInTheDocument();
    expect(screen.getByText('Test action')).toBeInTheDocument();
  });

  it('should display help text about closing with Esc', () => {
    render(
      <KeyboardShortcutsHelpModal
        isOpen={true}
        onClose={mockOnClose}
        shortcuts={mockShortcuts}
      />
    );

    // The text is split by the kbd element, so we need to check for parts
    expect(screen.getByText(/Press/i)).toBeInTheDocument();
    expect(screen.getByText(/to close this dialog/i)).toBeInTheDocument();
  });
});

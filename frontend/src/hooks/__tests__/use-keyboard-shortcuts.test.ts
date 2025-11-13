import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useKeyboardShortcuts, KeyboardShortcut } from '../use-keyboard-shortcuts';

describe('useKeyboardShortcuts', () => {
  let mockAction: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockAction = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should trigger action when correct key is pressed', () => {
    const shortcuts: KeyboardShortcut[] = [
      {
        key: '/',
        action: mockAction,
        description: 'Focus search',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', { key: '/' });
    window.dispatchEvent(event);

    expect(mockAction).toHaveBeenCalledTimes(1);
  });

  it('should trigger action with ctrl modifier', () => {
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 's',
        ctrl: true,
        action: mockAction,
        description: 'Save',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', { key: 's', ctrlKey: true });
    window.dispatchEvent(event);

    expect(mockAction).toHaveBeenCalledTimes(1);
  });

  it('should trigger action with shift modifier', () => {
    const shortcuts: KeyboardShortcut[] = [
      {
        key: '?',
        shift: true,
        action: mockAction,
        description: 'Show help',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', { key: '?', shiftKey: true });
    window.dispatchEvent(event);

    expect(mockAction).toHaveBeenCalledTimes(1);
  });

  it('should not trigger action when wrong key is pressed', () => {
    const shortcuts: KeyboardShortcut[] = [
      {
        key: '/',
        action: mockAction,
        description: 'Focus search',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', { key: 'a' });
    window.dispatchEvent(event);

    expect(mockAction).not.toHaveBeenCalled();
  });

  it('should not trigger action when typing in input field', () => {
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'a',
        action: mockAction,
        description: 'Test action',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();

    const event = new KeyboardEvent('keydown', { key: 'a', bubbles: true });
    input.dispatchEvent(event);

    expect(mockAction).not.toHaveBeenCalled();

    document.body.removeChild(input);
  });

  it('should allow "/" to work even in input fields', () => {
    const shortcuts: KeyboardShortcut[] = [
      {
        key: '/',
        action: mockAction,
        description: 'Focus search',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();

    const event = new KeyboardEvent('keydown', { key: '/', bubbles: true });
    Object.defineProperty(event, 'target', { value: input, enumerable: true });
    window.dispatchEvent(event);

    expect(mockAction).toHaveBeenCalledTimes(1);

    document.body.removeChild(input);
  });

  it('should not trigger when disabled', () => {
    const shortcuts: KeyboardShortcut[] = [
      {
        key: '/',
        action: mockAction,
        description: 'Focus search',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts, { enabled: false }));

    const event = new KeyboardEvent('keydown', { key: '/' });
    window.dispatchEvent(event);

    expect(mockAction).not.toHaveBeenCalled();
  });

  it('should handle multiple shortcuts', () => {
    const action1 = vi.fn();
    const action2 = vi.fn();

    const shortcuts: KeyboardShortcut[] = [
      {
        key: '/',
        action: action1,
        description: 'Focus search',
      },
      {
        key: '?',
        shift: true,
        action: action2,
        description: 'Show help',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event1 = new KeyboardEvent('keydown', { key: '/' });
    window.dispatchEvent(event1);

    expect(action1).toHaveBeenCalledTimes(1);
    expect(action2).not.toHaveBeenCalled();

    const event2 = new KeyboardEvent('keydown', { key: '?', shiftKey: true });
    window.dispatchEvent(event2);

    expect(action1).toHaveBeenCalledTimes(1);
    expect(action2).toHaveBeenCalledTimes(1);
  });

  it('should prevent default when preventDefault is true', () => {
    const shortcuts: KeyboardShortcut[] = [
      {
        key: '/',
        action: mockAction,
        description: 'Focus search',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts, { preventDefault: true }));

    const event = new KeyboardEvent('keydown', { key: '/' });
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault');
    window.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });

  it('should handle Escape key', () => {
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'Escape',
        action: mockAction,
        description: 'Close modal',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', { key: 'Escape' });
    window.dispatchEvent(event);

    expect(mockAction).toHaveBeenCalledTimes(1);
  });

  it('should handle arrow keys', () => {
    const upAction = vi.fn();
    const downAction = vi.fn();

    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'ArrowUp',
        action: upAction,
        description: 'Navigate up',
      },
      {
        key: 'ArrowDown',
        action: downAction,
        description: 'Navigate down',
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const upEvent = new KeyboardEvent('keydown', { key: 'ArrowUp' });
    window.dispatchEvent(upEvent);

    expect(upAction).toHaveBeenCalledTimes(1);
    expect(downAction).not.toHaveBeenCalled();

    const downEvent = new KeyboardEvent('keydown', { key: 'ArrowDown' });
    window.dispatchEvent(downEvent);

    expect(upAction).toHaveBeenCalledTimes(1);
    expect(downAction).toHaveBeenCalledTimes(1);
  });
});

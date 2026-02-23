/**
 * Tests for useKeyboardShortcut hook.
 */

import { renderHook, act } from '@testing-library/react';
import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut';

function fireKey(key: string, options: Partial<KeyboardEventInit> = {}) {
  act(() => {
    window.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, ...options }));
  });
}

describe('useKeyboardShortcut', () => {
  it('calls handler on matching key', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut({ key: 'k', handler }));
    fireKey('k');
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('does not call handler for non-matching key', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut({ key: 'k', handler }));
    fireKey('j');
    expect(handler).not.toHaveBeenCalled();
  });

  it('requires specified modifiers', () => {
    const handler = vi.fn();
    renderHook(() =>
      useKeyboardShortcut({ key: 'k', modifiers: ['ctrl'], handler }),
    );

    // Without modifier — should not fire
    fireKey('k');
    expect(handler).not.toHaveBeenCalled();

    // With modifier — should fire
    fireKey('k', { ctrlKey: true });
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('handles meta modifier', () => {
    const handler = vi.fn();
    renderHook(() =>
      useKeyboardShortcut({ key: 'p', modifiers: ['meta'], handler }),
    );
    fireKey('p', { metaKey: true });
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('does not call handler when enabled=false', () => {
    const handler = vi.fn();
    renderHook(() =>
      useKeyboardShortcut({ key: 'k', handler, enabled: false }),
    );
    fireKey('k');
    expect(handler).not.toHaveBeenCalled();
  });

  it('is case insensitive', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut({ key: 'K', handler }));
    fireKey('k');
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('rejects when extra modifiers are pressed', () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut({ key: 'k', handler }));
    fireKey('k', { ctrlKey: true });
    expect(handler).not.toHaveBeenCalled();
  });

  it('cleans up listener on unmount', () => {
    const handler = vi.fn();
    const { unmount } = renderHook(() =>
      useKeyboardShortcut({ key: 'k', handler }),
    );
    unmount();
    fireKey('k');
    expect(handler).not.toHaveBeenCalled();
  });
});

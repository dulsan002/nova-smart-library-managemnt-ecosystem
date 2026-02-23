/**
 * useKeyboardShortcut — registers global keyboard shortcuts.
 */

import { useEffect } from 'react';

type Modifier = 'ctrl' | 'meta' | 'alt' | 'shift';

interface ShortcutOptions {
  key: string;
  modifiers?: Modifier[];
  handler: (e: KeyboardEvent) => void;
  enabled?: boolean;
}

export function useKeyboardShortcut({
  key,
  modifiers = [],
  handler,
  enabled = true,
}: ShortcutOptions) {
  useEffect(() => {
    if (!enabled) return;

    function onKeyDown(e: KeyboardEvent) {
      const matchKey = e.key.toLowerCase() === key.toLowerCase();
      const matchCtrl = modifiers.includes('ctrl') ? e.ctrlKey : !e.ctrlKey;
      const matchMeta = modifiers.includes('meta') ? e.metaKey : !e.metaKey;
      const matchAlt = modifiers.includes('alt') ? e.altKey : !e.altKey;
      const matchShift = modifiers.includes('shift') ? e.shiftKey : !e.shiftKey;

      if (matchKey && matchCtrl && matchMeta && matchAlt && matchShift) {
        e.preventDefault();
        handler(e);
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [key, modifiers, handler, enabled]);
}

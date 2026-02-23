/**
 * useDocumentTitle — sets the browser document title.
 */

import { useEffect } from 'react';

export function useDocumentTitle(title: string) {
  useEffect(() => {
    const prev = document.title;
    document.title = title ? `${title} — NovaLib` : 'NovaLib';
    return () => {
      document.title = prev;
    };
  }, [title]);
}

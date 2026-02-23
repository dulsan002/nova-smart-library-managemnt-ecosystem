/**
 * Tests for useDocumentTitle hook.
 */

import { renderHook } from '@testing-library/react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';

describe('useDocumentTitle', () => {
  const originalTitle = document.title;

  afterEach(() => {
    document.title = originalTitle;
  });

  it('sets document title with NovaLib suffix', () => {
    renderHook(() => useDocumentTitle('Dashboard'));
    expect(document.title).toBe('Dashboard — NovaLib');
  });

  it('sets just NovaLib when title is empty', () => {
    renderHook(() => useDocumentTitle(''));
    expect(document.title).toBe('NovaLib');
  });

  it('updates title when value changes', () => {
    const { rerender } = renderHook(
      ({ title }) => useDocumentTitle(title),
      { initialProps: { title: 'Page A' } },
    );
    expect(document.title).toBe('Page A — NovaLib');

    rerender({ title: 'Page B' });
    expect(document.title).toBe('Page B — NovaLib');
  });

  it('restores previous title on unmount', () => {
    document.title = 'Original';
    const { unmount } = renderHook(() => useDocumentTitle('Temp'));
    expect(document.title).toBe('Temp — NovaLib');

    unmount();
    expect(document.title).toBe('Original');
  });
});

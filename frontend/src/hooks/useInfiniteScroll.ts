/**
 * useInfiniteScroll — triggers a callback when the user scrolls near the bottom.
 */

import { useEffect, useRef, useCallback } from 'react';

interface UseInfiniteScrollOptions {
  hasMore: boolean;
  loading: boolean;
  onLoadMore: () => void;
  threshold?: number; // px from bottom
}

export function useInfiniteScroll({
  hasMore,
  loading,
  onLoadMore,
  threshold = 200,
}: UseInfiniteScrollOptions) {
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const entry = entries[0];
      if (entry?.isIntersecting && hasMore && !loading) {
        onLoadMore();
      }
    },
    [hasMore, loading, onLoadMore],
  );

  useEffect(() => {
    const node = sentinelRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(handleObserver, {
      rootMargin: `${threshold}px`,
    });

    observer.observe(node);
    return () => observer.disconnect();
  }, [handleObserver, threshold]);

  return { sentinelRef };
}

/**
 * SearchOverlay — global ⌘K / Ctrl+K quick-search overlay.
 * Uses auto-suggest for live results and navigates to book detail or full search.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLazyQuery } from '@apollo/client';
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  BookOpenIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import { useUIStore } from '@/stores/uiStore';
import { SEARCH_BOOKS } from '@/graphql/queries/intelligence';
import { cn } from '@/lib/utils';

interface SearchResult {
  bookId: string;
  title: string;
  subtitle?: string;
  authorNames?: string[];
  score?: number;
  snippet?: string;
}

export function SearchOverlay() {
  const navigate = useNavigate();
  const open = useUIStore((s) => s.searchOverlayOpen);
  const close = useUIStore((s) => s.setSearchOverlayOpen);
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(0);

  const [search, { data, loading }] = useLazyQuery(SEARCH_BOOKS, {
    fetchPolicy: 'network-only',
  });

  const results: SearchResult[] = data?.searchBooks?.results ?? [];

  // ── Global ⌘K / Ctrl+K listener ──────────────────────────────
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (open) {
          close(false);
        } else {
          close(true);
        }
      }
      if (e.key === 'Escape' && open) {
        close(false);
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, close]);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setQuery('');
      setSelectedIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) return;
    const timer = setTimeout(() => {
      search({ variables: { query: query.trim(), pageSize: 8 } });
    }, 250);
    return () => clearTimeout(timer);
  }, [query, search]);

  // Reset selection on results change
  useEffect(() => {
    setSelectedIdx(0);
  }, [results.length]);

  const goToResult = useCallback(
    (result: SearchResult) => {
      close(false);
      navigate(`/catalog/${result.bookId}`);
    },
    [close, navigate],
  );

  const goToFullSearch = useCallback(() => {
    close(false);
    navigate(`/search?q=${encodeURIComponent(query)}`);
  }, [close, navigate, query]);

  // Keyboard navigation inside the overlay
  function handleKeyDown(e: React.KeyboardEvent) {
    const total = results.length + (query.trim() ? 1 : 0); // +1 for "View all"
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIdx((i) => (i + 1) % total);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIdx((i) => (i - 1 + total) % total);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIdx < results.length && results[selectedIdx]) {
        goToResult(results[selectedIdx]);
      } else if (query.trim()) {
        goToFullSearch();
      }
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh]">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => close(false)}
      />

      {/* Dialog */}
      <div className="relative w-full max-w-xl animate-fade-in rounded-2xl border border-nova-border bg-nova-surface shadow-2xl">
        {/* Search input */}
        <div className="flex items-center gap-3 border-b border-nova-border px-4 py-3">
          <MagnifyingGlassIcon className="h-5 w-5 flex-shrink-0 text-nova-text-muted" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search books, authors, topics…"
            className="flex-1 bg-transparent text-base text-nova-text placeholder:text-nova-text-muted outline-none"
            autoComplete="off"
            spellCheck={false}
          />
          <div className="flex items-center gap-1.5">
            <kbd className="rounded-md border border-nova-border bg-nova-bg px-1.5 py-0.5 text-[10px] font-semibold text-nova-text-muted">
              ESC
            </kbd>
            <button
              onClick={() => close(false)}
              className="rounded-lg p-1 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text"
              aria-label="Close search"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto nova-scrollbar">
          {!query.trim() ? (
            <div className="px-4 py-8 text-center text-sm text-nova-text-muted">
              Start typing to search the library catalog…
            </div>
          ) : loading && results.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-nova-text-muted">
              <div className="mx-auto h-5 w-5 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
              <p className="mt-2">Searching…</p>
            </div>
          ) : results.length === 0 && !loading ? (
            <div className="px-4 py-8 text-center text-sm text-nova-text-muted">
              No results found for &ldquo;{query}&rdquo;
            </div>
          ) : (
            <ul className="py-2">
              {results.map((r, idx) => (
                <li key={r.bookId}>
                  <button
                    onClick={() => goToResult(r)}
                    onMouseEnter={() => setSelectedIdx(idx)}
                    className={cn(
                      'flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors',
                      idx === selectedIdx
                        ? 'bg-primary-50 dark:bg-primary-900/20'
                        : 'hover:bg-nova-surface-hover',
                    )}
                  >
                    <BookOpenIcon className="h-5 w-5 flex-shrink-0 text-primary-500" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-nova-text">
                        {r.title}
                      </p>
                      {r.authorNames && r.authorNames.length > 0 && (
                        <p className="truncate text-xs text-nova-text-muted">
                          {r.authorNames.join(', ')}
                        </p>
                      )}
                    </div>
                    {idx === selectedIdx && (
                      <kbd className="shrink-0 rounded-md border border-nova-border bg-nova-bg px-1.5 py-0.5 text-[10px] font-semibold text-nova-text-muted">
                        ↵
                      </kbd>
                    )}
                  </button>
                </li>
              ))}

              {/* "View all results" row */}
              {query.trim() && (
                <li>
                  <button
                    onClick={goToFullSearch}
                    onMouseEnter={() => setSelectedIdx(results.length)}
                    className={cn(
                      'flex w-full items-center gap-3 border-t border-nova-border px-4 py-2.5 text-left transition-colors',
                      selectedIdx === results.length
                        ? 'bg-primary-50 dark:bg-primary-900/20'
                        : 'hover:bg-nova-surface-hover',
                    )}
                  >
                    <ArrowRightIcon className="h-5 w-5 flex-shrink-0 text-nova-text-muted" />
                    <span className="text-sm font-medium text-nova-text">
                      View all results for &ldquo;{query}&rdquo;
                    </span>
                    {selectedIdx === results.length && (
                      <kbd className="ml-auto shrink-0 rounded-md border border-nova-border bg-nova-bg px-1.5 py-0.5 text-[10px] font-semibold text-nova-text-muted">
                        ↵
                      </kbd>
                    )}
                  </button>
                </li>
              )}
            </ul>
          )}
        </div>

        {/* Footer hint */}
        <div className="flex items-center justify-between border-t border-nova-border px-4 py-2 text-[11px] text-nova-text-muted">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-nova-border bg-nova-bg px-1 py-0.5 font-semibold">↑↓</kbd>
              navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-nova-border bg-nova-bg px-1 py-0.5 font-semibold">↵</kbd>
              open
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-nova-border bg-nova-bg px-1 py-0.5 font-semibold">esc</kbd>
              close
            </span>
          </div>
          {loading && (
            <div className="h-3 w-3 animate-spin rounded-full border border-primary-500 border-t-transparent" />
          )}
        </div>
      </div>
    </div>
  );
}

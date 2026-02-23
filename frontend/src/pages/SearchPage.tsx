/**
 * SearchPage — hybrid search with auto-suggest, facets, and result display.
 */

import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useLazyQuery, useQuery } from '@apollo/client';
import {
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle, useDebounce } from '@/hooks';
import { SEARCH_BOOKS, AUTO_SUGGEST } from '@/graphql/queries/intelligence';
import { SearchInput } from '@/components/ui/SearchInput';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';

export default function SearchPage() {
  useDocumentTitle('Search');
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQ = searchParams.get('q') || '';

  const [query, setQuery] = useState(initialQ);
  const debouncedQuery = useDebounce(query, 300);

  // Auto-suggest
  const { data: suggestData, loading: suggestLoading, error: suggestError } = useQuery(AUTO_SUGGEST, {
    variables: { prefix: debouncedQuery, limit: 8 },
    skip: debouncedQuery.length < 2,
  });

  if (suggestError) {
    console.warn('Auto-suggest error:', suggestError.message);
  }

  const suggestions = (suggestData?.autoSuggest ?? []).map((s: any, i: number) => ({
    id: `${i}`,
    text: s.text ?? s,
    category: s.category,
  }));

  // Search results
  const [doSearch, { data: searchData, loading: searching, error: searchError }] = useLazyQuery(SEARCH_BOOKS);
  const results = searchData?.searchBooks?.results ?? [];

  const executeSearch = useCallback(
    (q: string) => {
      if (!q.trim()) return;
      setSearchParams({ q });
      doSearch({ variables: { query: q, pageSize: 50 } });
    },
    [doSearch, setSearchParams],
  );

  // Run search on initial load with URL query
  useEffect(() => {
    if (initialQ) executeSearch(initialQ);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handleSuggestionClick(suggestion: { id: string; text: string }) {
    setQuery(suggestion.text);
    executeSearch(suggestion.text);
  }

  function handleResultClick(_bookId: string) {
    // logSearchClick requires a searchLogId which we don't track yet
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-nova-text">Search</h1>
        <p className="text-sm text-nova-text-secondary">
          AI-powered hybrid search across the entire collection
        </p>
      </div>

      {/* Search bar */}
      <SearchInput
        value={query}
        onChange={setQuery}
        onSubmit={executeSearch}
        suggestions={suggestions}
        onSuggestionClick={handleSuggestionClick}
        showSuggestions={debouncedQuery.length >= 2 && !searching}
        loading={suggestLoading}
        placeholder="Search by title, author, topic, or ask a question…"
        size="lg"
        autoFocus
      />

      {/* Results */}
      {searchError ? (
        <div className="flex flex-col items-center py-12 text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-amber-500" />
          <h3 className="mt-3 text-lg font-semibold text-nova-text">Search failed</h3>
          <p className="mt-1 max-w-md text-sm text-nova-text-secondary">
            {searchError.message || 'Something went wrong. Please try again.'}
          </p>
          <button
            onClick={() => executeSearch(query)}
            className="mt-4 text-sm font-medium text-primary-600 hover:text-primary-500"
          >
            Try again
          </button>
        </div>
      ) : searching ? (
        <LoadingOverlay message="Searching…" />
      ) : results.length > 0 ? (
        <div>
          <p className="mb-4 text-sm text-nova-text-secondary">
            {results.length} result{results.length !== 1 ? 's' : ''} found
          </p>
          <div className="space-y-3">
            {results.map((result: any) => (
              <Link
                key={result.bookId}
                to={`/catalog/${result.bookId}`}
                onClick={() => handleResultClick(result.bookId)}
              >
                <Card hoverable className="flex gap-4">
                  {/* Info */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between">
                      <div className="min-w-0">
                        <h3 className="truncate font-semibold text-nova-text">
                          {result.title}
                        </h3>
                        <p className="text-sm text-nova-text-muted">
                          {result.authorNames?.join(', ') ?? ''}
                        </p>
                      </div>
                      {result.score !== undefined && (
                        <Badge variant="primary" size="xs" className="ml-2">
                          {Math.round(result.score * 100)}% relevance
                        </Badge>
                      )}
                    </div>
                    {result.snippet && (
                      <p className="mt-1 line-clamp-2 text-sm text-nova-text-secondary">
                        {result.snippet}
                      </p>
                    )}
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      ) : searchParams.get('q') ? (
        <EmptyState
          icon={<MagnifyingGlassIcon />}
          title="No results found"
          description={`We couldn\u2019t find anything matching "${searchParams.get('q')}". Try different keywords.`}
        />
      ) : (
        <div className="flex flex-col items-center py-16 text-center">
          <MagnifyingGlassIcon className="h-16 w-16 text-nova-text-muted" />
          <h3 className="mt-4 text-lg font-semibold text-nova-text">
            Start your search
          </h3>
          <p className="mt-1 max-w-md text-sm text-nova-text-secondary">
            Type a book title, author name, topic, or even a question. Our AI-powered
            search will find the most relevant results.
          </p>
        </div>
      )}
    </div>
  );
}

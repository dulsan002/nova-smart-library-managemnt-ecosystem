/**
 * SearchPage — hybrid search with AI-powered answers, auto-suggest, and result display.
 */

import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useLazyQuery, useQuery } from '@apollo/client';
import {
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
  BookOpenIcon,
  StarIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle, useDebounce } from '@/hooks';
import { SEARCH_BOOKS, AUTO_SUGGEST, AI_SEARCH } from '@/graphql/queries/intelligence';
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
  const [hasSearched, setHasSearched] = useState(!!initialQ);
  const debouncedQuery = useDebounce(query, 300);

  // Auto-suggest — only when user is typing (not after a search was submitted)
  const shouldSuggest = debouncedQuery.length >= 2 && !hasSearched;
  const { data: suggestData, loading: suggestLoading, error: suggestError } = useQuery(AUTO_SUGGEST, {
    variables: { prefix: debouncedQuery, limit: 8 },
    skip: !shouldSuggest,
  });

  if (suggestError) {
    console.warn('Auto-suggest error:', suggestError.message);
  }

  const suggestions = shouldSuggest
    ? (suggestData?.autoSuggest ?? []).map((s: any, i: number) => ({
        id: `${i}`,
        text: s.text ?? s,
        category: s.category,
      }))
    : [];

  // Search results (hybrid)
  const [doSearch, { data: searchData, loading: searching, error: searchError }] = useLazyQuery(SEARCH_BOOKS);
  const results = searchData?.searchBooks?.results ?? [];

  // AI-powered search
  const [doAiSearch, { data: aiData, loading: aiSearching }] = useLazyQuery(AI_SEARCH, {
    fetchPolicy: 'network-only',
  });
  const aiResult = aiData?.aiSearch;

  const executeSearch = useCallback(
    (q: string) => {
      if (!q.trim()) return;
      setHasSearched(true);
      setSearchParams({ q });
      doSearch({ variables: { query: q, pageSize: 50 } });
      doAiSearch({ variables: { query: q } });
    },
    [doSearch, doAiSearch, setSearchParams],
  );

  // When user changes the query text, reset hasSearched so suggestions reappear
  const handleQueryChange = useCallback(
    (val: string) => {
      setQuery(val);
      if (hasSearched) setHasSearched(false);
    },
    [hasSearched],
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
        onChange={handleQueryChange}
        onSubmit={executeSearch}
        suggestions={suggestions}
        onSuggestionClick={handleSuggestionClick}
        showSuggestions={shouldSuggest && suggestions.length > 0}
        loading={suggestLoading}
        placeholder="Search by title, author, topic, or ask a question…"
        size="lg"
        autoFocus
      />

      {/* AI Answer Panel */}
      {(aiSearching || aiResult) && searchParams.get('q') && (
        <div className="rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-5 shadow-sm dark:border-indigo-800 dark:from-indigo-950/30 dark:via-gray-900 dark:to-purple-950/20">
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 shadow-sm">
              <SparklesIcon className="h-4 w-4 text-white" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-indigo-900 dark:text-indigo-200">
                AI Assistant
              </span>
              {aiResult?.modelUsed && (
                <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-medium text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-300">
                  {aiResult.modelUsed}
                </span>
              )}
            </div>
          </div>

          {aiSearching ? (
            <div className="flex items-center gap-3 py-4">
              <div className="flex gap-1">
                <span className="h-2 w-2 animate-bounce rounded-full bg-indigo-400" style={{ animationDelay: '0ms' }} />
                <span className="h-2 w-2 animate-bounce rounded-full bg-indigo-400" style={{ animationDelay: '150ms' }} />
                <span className="h-2 w-2 animate-bounce rounded-full bg-indigo-400" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-sm text-indigo-600 dark:text-indigo-300">
                Thinking…
              </span>
            </div>
          ) : aiResult?.error ? (
            <p className="text-sm text-amber-600 dark:text-amber-400">
              {aiResult.error}
            </p>
          ) : aiResult?.answer ? (
            <div className="space-y-4">
              <p className="whitespace-pre-line text-sm leading-relaxed text-gray-700 dark:text-gray-300">
                {aiResult.answer}
              </p>

              {/* AI Source Books */}
              {aiResult.sources?.length > 0 && (
                <div className="mt-3 border-t border-indigo-100 pt-3 dark:border-indigo-800">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-indigo-500 dark:text-indigo-400">
                    Referenced Books
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {aiResult.sources.slice(0, 5).map((src: any) => (
                      <Link
                        key={src.bookId}
                        to={`/catalog/${src.bookId}`}
                        className="group inline-flex items-center gap-1.5 rounded-lg border border-indigo-100 bg-white px-3 py-1.5 text-xs font-medium text-indigo-700 shadow-sm transition-all hover:border-indigo-300 hover:shadow-md dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-300 dark:hover:border-indigo-600"
                      >
                        <BookOpenIcon className="h-3.5 w-3.5 text-indigo-400" />
                        <span className="max-w-[200px] truncate">{src.title}</span>
                        {src.rating > 0 && (
                          <span className="ml-1 inline-flex items-center gap-0.5 text-amber-500">
                            <StarIcon className="h-3 w-3 fill-current" />
                            {src.rating.toFixed(1)}
                          </span>
                        )}
                        {src.availableCopies > 0 && (
                          <span className="ml-1 rounded bg-green-100 px-1 py-0.5 text-[10px] text-green-700 dark:bg-green-900/30 dark:text-green-400">
                            Available
                          </span>
                        )}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

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
          <div className="relative mb-4">
            <MagnifyingGlassIcon className="h-16 w-16 text-nova-text-muted" />
            <SparklesIcon className="absolute -right-2 -top-2 h-6 w-6 text-indigo-500" />
          </div>
          <h3 className="mt-4 text-lg font-semibold text-nova-text">
            Start your search
          </h3>
          <p className="mt-1 max-w-md text-sm text-nova-text-secondary">
            Type a book title, author name, topic, or even a question. Our AI assistant
            will find the most relevant results and give you a helpful answer.
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {['Recommend a good sci-fi book', 'Books by J.K. Rowling', 'Best books about machine learning'].map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => { setQuery(suggestion); executeSearch(suggestion); }}
                className="rounded-full border border-nova-border bg-nova-surface px-3 py-1.5 text-xs text-nova-text-secondary transition-colors hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 dark:hover:border-indigo-700 dark:hover:bg-indigo-950/30 dark:hover:text-indigo-300"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

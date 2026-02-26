/**
 * CatalogPage — Advanced library catalog with sidebar filters, hero banner,
 * format badges, sort controls, and grid/list views.
 *
 * Inspired by NYPL's catalog UX — persistent sidebar, format indicators,
 * and rich book cards — but with a modern Nova design system.
 */

import { useState, useMemo, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@apollo/client';
import {
  BookOpenIcon,
  Squares2X2Icon,
  ListBulletIcon,
  XMarkIcon,
  MagnifyingGlassIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  SparklesIcon,
  FireIcon,
  StarIcon,
  ClockIcon,
  ArrowsUpDownIcon,
  MusicalNoteIcon,
  DocumentTextIcon,
  GlobeAltIcon,
  AdjustmentsHorizontalIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { BookOpenIcon as BookOpenSolid, StarIcon as StarSolid } from '@heroicons/react/24/solid';
import { useDocumentTitle, useDebounce } from '@/hooks';
import { GET_BOOKS, GET_CATEGORIES } from '@/graphql/queries/catalog';
import { Button } from '@/components/ui/Button';
import { SearchInput } from '@/components/ui/SearchInput';
import { Pagination } from '@/components/ui/Pagination';
import { EmptyState } from '@/components/ui/EmptyState';
import { SkeletonCard } from '@/components/ui/Spinner';
import { Select } from '@/components/ui/Select';
import { ITEMS_PER_PAGE, BOOK_LANGUAGES } from '@/lib/constants';

type ViewMode = 'grid' | 'list';
type SortOption = '-created_at' | 'title' | '-total_borrows' | '-average_rating';

const SORT_OPTIONS: { value: SortOption; label: string; icon: React.ReactNode }[] = [
  { value: '-created_at', label: 'Newest First', icon: <ClockIcon className="h-4 w-4" /> },
  { value: '-total_borrows', label: 'Most Popular', icon: <FireIcon className="h-4 w-4" /> },
  { value: '-average_rating', label: 'Highest Rated', icon: <StarIcon className="h-4 w-4" /> },
  { value: 'title', label: 'Title A–Z', icon: <ArrowsUpDownIcon className="h-4 w-4" /> },
];

const QUICK_FILTERS = [
  { key: 'all', label: 'All Books', icon: <BookOpenIcon className="h-4 w-4" /> },
  { key: 'available', label: 'Available Now', icon: <CheckCircleIcon className="h-4 w-4" /> },
  { key: 'new', label: 'New Arrivals', icon: <SparklesIcon className="h-4 w-4" /> },
  { key: 'popular', label: 'Most Popular', icon: <FireIcon className="h-4 w-4" /> },
  { key: 'top-rated', label: 'Top Rated', icon: <StarIcon className="h-4 w-4" /> },
];

export default function CatalogPage() {
  useDocumentTitle('Catalog — Nova Library');

  const [searchParams, setSearchParams] = useSearchParams();
  const [view, setView] = useState<ViewMode>('grid');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const resultsRef = useRef<HTMLDivElement>(null);

  // Filters from URL
  const searchQ = searchParams.get('q') || '';
  const categoryId = searchParams.get('category') || '';
  const language = searchParams.get('language') || '';
  const sortBy = (searchParams.get('sort') as SortOption) || '-created_at';
  const quickFilter = searchParams.get('filter') || 'all';
  const afterCursor = searchParams.get('after') || undefined;

  const [localSearch, setLocalSearch] = useState(searchQ);
  const debouncedSearch = useDebounce(localSearch, 400);

  // Fetch categories (hierarchical)
  const { data: catData } = useQuery(GET_CATEGORIES, { variables: { rootOnly: true } });
  const rootCategories = catData?.categories ?? [];

  // Compute query variables based on quick filter
  const queryVars = useMemo(() => {
    const vars: any = {
      first: ITEMS_PER_PAGE,
      after: afterCursor || undefined,
      query: debouncedSearch || undefined,
      categoryId: categoryId || undefined,
      language: language || undefined,
      orderBy: sortBy,
    };

    switch (quickFilter) {
      case 'available':
        vars.availableOnly = true;
        break;
      case 'new':
        vars.orderBy = '-created_at';
        break;
      case 'popular':
        vars.orderBy = '-total_borrows';
        break;
      case 'top-rated':
        vars.orderBy = '-average_rating';
        break;
    }

    return vars;
  }, [afterCursor, debouncedSearch, categoryId, language, sortBy, quickFilter]);

  // Fetch books
  const { data, loading, previousData } = useQuery(GET_BOOKS, {
    variables: queryVars,
    fetchPolicy: 'cache-and-network',
  });

  const booksData = data ?? previousData;
  const edges = booksData?.books?.edges ?? [];
  const books = edges.map((e: any) => e.node).filter(Boolean);
  const pageInfo = booksData?.books?.pageInfo ?? {
    hasNextPage: false,
    hasPreviousPage: false,
  };
  const totalCount = booksData?.books?.totalCount ?? 0;

  const languageOptions = [
    { value: '', label: 'All Languages' },
    ...BOOK_LANGUAGES.map((l) => ({ value: l.code, label: l.label })),
  ];

  function updateParam(key: string, value: string) {
    const p = new URLSearchParams(searchParams);
    if (value) p.set(key, value);
    else p.delete(key);
    p.delete('after');
    p.delete('before');
    setSearchParams(p);
  }

  function handleNext() {
    const p = new URLSearchParams(searchParams);
    p.set('after', pageInfo.endCursor || '');
    p.delete('before');
    setSearchParams(p);
    resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function handlePrev() {
    const p = new URLSearchParams(searchParams);
    p.set('before', pageInfo.startCursor || '');
    p.delete('after');
    setSearchParams(p);
    resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function toggleCategory(id: string) {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function selectCategory(id: string) {
    updateParam('category', categoryId === id ? '' : id);
  }

  const activeFilterCount = [categoryId, language].filter(Boolean).length +
    (quickFilter !== 'all' ? 1 : 0);

  const selectedCategoryName = useMemo(() => {
    for (const root of rootCategories) {
      if (root.id === categoryId) return root.name;
      for (const child of root.children ?? []) {
        if (child.id === categoryId) return child.name;
      }
    }
    return null;
  }, [rootCategories, categoryId]);

  return (
    <div className="animate-fade-in">
      {/* ═══════════════════ Hero Banner ═══════════════════ */}
      <div className="relative mb-8 overflow-hidden rounded-2xl bg-gradient-to-br from-primary-600 via-primary-700 to-indigo-800 px-6 py-8 sm:px-10 sm:py-12">
        <div className="absolute inset-0 opacity-10">
          <svg className="h-full w-full" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="book-pattern" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
                <rect x="8" y="4" width="24" height="32" rx="2" fill="currentColor" opacity="0.3" />
                <rect x="10" y="6" width="20" height="28" rx="1" fill="currentColor" opacity="0.15" />
              </pattern>
            </defs>
            <rect width="400" height="400" fill="url(#book-pattern)" />
          </svg>
        </div>
        <div className="relative z-10 max-w-2xl">
          <h1 className="text-3xl font-extrabold text-white sm:text-4xl tracking-tight">
            Explore Our Collection
          </h1>
          <p className="mt-3 text-lg text-primary-100">
            Discover {totalCount.toLocaleString()} books across multiple formats — physical copies,
            e-books, and audiobooks
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2 text-sm text-primary-200">
              <BookOpenSolid className="h-5 w-5 text-white/80" />
              <span className="font-medium text-white">{totalCount}</span> Books
            </div>
            <div className="flex items-center gap-2 text-sm text-primary-200">
              <DocumentTextIcon className="h-5 w-5 text-white/80" />
              <span className="font-medium text-white">E-Books</span> Available
            </div>
            <div className="flex items-center gap-2 text-sm text-primary-200">
              <MusicalNoteIcon className="h-5 w-5 text-white/80" />
              <span className="font-medium text-white">Audiobooks</span> Available
            </div>
          </div>
        </div>
        {/* Decorative book stack */}
        <div className="absolute -right-6 -bottom-6 hidden opacity-20 lg:block">
          <div className="flex gap-2 rotate-[-8deg]">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-40 w-28 rounded-lg bg-white/30" style={{ transform: `translateY(${i * 8}px)` }} />
            ))}
          </div>
        </div>
      </div>

      {/* ═══════════════════ Search Bar ═══════════════════ */}
      <div className="mb-6">
        <div className="relative">
          <SearchInput
            value={localSearch}
            onChange={(v) => {
              setLocalSearch(v);
              if (!v) updateParam('q', '');
            }}
            onSubmit={(v) => updateParam('q', v)}
            placeholder="Search by title, author, ISBN, or keyword…"
            size="md"
          />
        </div>
      </div>

      {/* ═══════════════════ Quick Filters ═══════════════════ */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        {QUICK_FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => updateParam('filter', f.key === 'all' ? '' : f.key)}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-all ${
              (quickFilter === f.key || (f.key === 'all' && quickFilter === 'all'))
                ? 'bg-primary-600 text-white shadow-md shadow-primary-600/25'
                : 'bg-nova-surface text-nova-text-secondary border border-nova-border hover:border-primary-300 hover:text-primary-600 dark:hover:border-primary-700'
            }`}
          >
            {f.icon}
            {f.label}
          </button>
        ))}
      </div>

      {/* ═══════════════════ Main Content: Sidebar + Results ═══════════════════ */}
      <div className="flex gap-6" ref={resultsRef}>
        {/* ─── Left Sidebar ─── */}
        <aside
          className={`hidden lg:block flex-shrink-0 transition-all duration-300 ${
            sidebarOpen ? 'w-64' : 'w-0 overflow-hidden'
          }`}
        >
          <div className="sticky top-4 space-y-5">
            {/* Category Tree */}
            <div className="rounded-xl border border-nova-border bg-nova-surface p-4">
              <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-nova-text-muted">
                Browse Categories
              </h3>
              <nav className="space-y-1">
                {/* All Categories option */}
                <button
                  onClick={() => selectCategory('')}
                  className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                    !categoryId
                      ? 'bg-primary-50 text-primary-700 font-semibold dark:bg-primary-900/20 dark:text-primary-400'
                      : 'text-nova-text-secondary hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <BookOpenIcon className="h-4 w-4 flex-shrink-0" />
                  All Categories
                </button>

                {rootCategories.map((cat: any) => {
                  const hasChildren = cat.children?.length > 0;
                  const isExpanded = expandedCategories.has(cat.id);
                  const isSelected = cat.id === categoryId;
                  const hasSelectedChild = cat.children?.some((c: any) => c.id === categoryId);

                  return (
                    <div key={cat.id}>
                      <div className="flex items-center">
                        {hasChildren && (
                          <button
                            onClick={() => toggleCategory(cat.id)}
                            className="p-1 text-nova-text-muted hover:text-nova-text rounded transition-colors"
                          >
                            {isExpanded ? (
                              <ChevronDownIcon className="h-3.5 w-3.5" />
                            ) : (
                              <ChevronRightIcon className="h-3.5 w-3.5" />
                            )}
                          </button>
                        )}
                        <button
                          onClick={() => selectCategory(cat.id)}
                          className={`flex-1 text-left rounded-lg px-3 py-2 text-sm transition-colors ${
                            isSelected || hasSelectedChild
                              ? 'bg-primary-50 text-primary-700 font-semibold dark:bg-primary-900/20 dark:text-primary-400'
                              : 'text-nova-text hover:bg-gray-100 dark:hover:bg-gray-800'
                          }`}
                        >
                          {cat.name}
                        </button>
                      </div>

                      {/* Children */}
                      {hasChildren && isExpanded && (
                        <div className="ml-5 mt-0.5 space-y-0.5 border-l-2 border-gray-200 pl-3 dark:border-gray-700">
                          {cat.children.map((child: any) => (
                            <button
                              key={child.id}
                              onClick={() => selectCategory(child.id)}
                              className={`w-full text-left rounded-lg px-3 py-1.5 text-sm transition-colors ${
                                child.id === categoryId
                                  ? 'bg-primary-50 text-primary-700 font-semibold dark:bg-primary-900/20 dark:text-primary-400'
                                  : 'text-nova-text-secondary hover:bg-gray-100 hover:text-nova-text dark:hover:bg-gray-800'
                              }`}
                            >
                              {child.name}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </nav>
            </div>

            {/* Language Filter */}
            <div className="rounded-xl border border-nova-border bg-nova-surface p-4">
              <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-nova-text-muted">
                Language
              </h3>
              <Select
                value={language}
                onChange={(v) => updateParam('language', v)}
                options={languageOptions}
                wrapperClassName="w-full"
              />
            </div>

            {/* Active Filters Summary */}
            {activeFilterCount > 0 && (
              <div className="rounded-xl border border-primary-200 bg-primary-50 p-4 dark:border-primary-800 dark:bg-primary-900/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-primary-700 dark:text-primary-400">
                    Active Filters
                  </span>
                  <button
                    onClick={() => {
                      const p = new URLSearchParams();
                      setSearchParams(p);
                      setLocalSearch('');
                    }}
                    className="text-xs font-medium text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-200"
                  >
                    Clear All
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {selectedCategoryName && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-primary-100 px-2.5 py-1 text-xs font-medium text-primary-700 dark:bg-primary-800/40 dark:text-primary-300">
                      {selectedCategoryName}
                      <button onClick={() => selectCategory('')} className="hover:text-primary-900">
                        <XMarkIcon className="h-3 w-3" />
                      </button>
                    </span>
                  )}
                  {language && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-primary-100 px-2.5 py-1 text-xs font-medium text-primary-700 dark:bg-primary-800/40 dark:text-primary-300">
                      {BOOK_LANGUAGES.find((l) => l.code === language)?.label ?? language}
                      <button onClick={() => updateParam('language', '')} className="hover:text-primary-900">
                        <XMarkIcon className="h-3 w-3" />
                      </button>
                    </span>
                  )}
                  {quickFilter !== 'all' && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-primary-100 px-2.5 py-1 text-xs font-medium text-primary-700 dark:bg-primary-800/40 dark:text-primary-300">
                      {QUICK_FILTERS.find((f) => f.key === quickFilter)?.label}
                      <button onClick={() => updateParam('filter', '')} className="hover:text-primary-900">
                        <XMarkIcon className="h-3 w-3" />
                      </button>
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* ─── Results Area ─── */}
        <div className="min-w-0 flex-1">
          {/* Toolbar: Results count + Sort + View toggle */}
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <p className="text-sm text-nova-text-secondary">
                <span className="font-semibold text-nova-text">{totalCount.toLocaleString()}</span>{' '}
                {totalCount === 1 ? 'book' : 'books'} found
                {selectedCategoryName && (
                  <span>
                    {' '}in <span className="font-medium text-primary-600 dark:text-primary-400">{selectedCategoryName}</span>
                  </span>
                )}
              </p>
              {loading && (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
              )}
            </div>

            <div className="flex items-center gap-2">
              {/* Sort dropdown */}
              <Select
                value={sortBy}
                onChange={(v) => updateParam('sort', v)}
                options={SORT_OPTIONS.map((s) => ({ value: s.value, label: s.label }))}
                wrapperClassName="min-w-[160px]"
              />

              {/* View toggle */}
              <div className="flex rounded-lg border border-nova-border bg-nova-surface p-0.5">
                <button
                  onClick={() => setView('grid')}
                  title="Grid view"
                  className={`rounded-md p-2 transition-colors ${
                    view === 'grid'
                      ? 'bg-primary-100 text-primary-600 dark:bg-primary-900/30'
                      : 'text-nova-text-muted hover:text-nova-text'
                  }`}
                >
                  <Squares2X2Icon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setView('list')}
                  title="List view"
                  className={`rounded-md p-2 transition-colors ${
                    view === 'list'
                      ? 'bg-primary-100 text-primary-600 dark:bg-primary-900/30'
                      : 'text-nova-text-muted hover:text-nova-text'
                  }`}
                >
                  <ListBulletIcon className="h-4 w-4" />
                </button>
              </div>

              {/* Mobile sidebar toggle */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="hidden rounded-lg border border-nova-border bg-nova-surface p-2 text-nova-text-muted hover:text-nova-text lg:inline-flex"
                title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
              >
                <AdjustmentsHorizontalIcon className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Mobile Filters (shown below lg breakpoint) */}
          <div className="mb-4 flex flex-wrap items-end gap-3 lg:hidden">
            <Select
              value={categoryId}
              onChange={(v) => updateParam('category', v)}
              options={[
                { value: '', label: 'All Categories' },
                ...rootCategories.flatMap((c: any) => [
                  { value: c.id, label: c.name },
                  ...(c.children ?? []).map((ch: any) => ({
                    value: ch.id,
                    label: `  └ ${ch.name}`,
                  })),
                ]),
              ]}
              label="Category"
              wrapperClassName="min-w-[160px]"
            />
            <Select
              value={language}
              onChange={(v) => updateParam('language', v)}
              options={languageOptions}
              label="Language"
              wrapperClassName="min-w-[140px]"
            />
          </div>

          {/* Results Grid/List */}
          {loading && !booksData ? (
            <div className={view === 'grid'
              ? 'grid gap-5 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4'
              : 'space-y-4'
            }>
              {Array.from({ length: 8 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : books.length === 0 ? (
            <EmptyState
              icon={<MagnifyingGlassIcon />}
              title="No books found"
              description={
                debouncedSearch
                  ? `No results for "${debouncedSearch}". Try a different search or adjust your filters.`
                  : 'No books match the current filters. Try broadening your search.'
              }
              action={
                activeFilterCount > 0 ? (
                  <Button
                    variant="secondary"
                    onClick={() => {
                      const p = new URLSearchParams();
                      setSearchParams(p);
                      setLocalSearch('');
                    }}
                  >
                    Clear All Filters
                  </Button>
                ) : undefined
              }
            />
          ) : view === 'grid' ? (
            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
              {books.map((book: any) => (
                <BookGridCard key={book.id} book={book} />
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {books.map((book: any) => (
                <BookListCard key={book.id} book={book} />
              ))}
            </div>
          )}

          {/* Pagination */}
          {books.length > 0 && (
            <div className="mt-6">
              <Pagination
                pageInfo={pageInfo}
                totalCount={totalCount}
                currentCount={books.length}
                onNext={handleNext}
                onPrev={handlePrev}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   BookGridCard — Rich card with cover, formats, and actions
   ═══════════════════════════════════════════════════════════ */

function BookGridCard({ book }: { book: any }) {
  return (
    <Link to={`/catalog/${book.id}`} className="group">
      <div className="overflow-hidden rounded-xl border border-nova-border bg-nova-surface shadow-sm transition-all duration-200 hover:shadow-lg hover:border-primary-300 hover:-translate-y-0.5 dark:hover:border-primary-700">
        {/* Cover with overlay */}
        <div className="relative aspect-[3/4] w-full overflow-hidden bg-gray-100 dark:bg-gray-800">
          {book.coverImageUrl ? (
            <img
              src={book.coverImageUrl}
              alt={book.title}
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
            />
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900">
              <BookOpenIcon className="h-12 w-12 text-gray-300 dark:text-gray-600" />
              <span className="text-xs text-gray-400 dark:text-gray-500 font-medium px-4 text-center leading-tight">
                {book.title}
              </span>
            </div>
          )}

          {/* Availability overlay badge */}
          <div className="absolute top-2 right-2">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide backdrop-blur-md ${
                book.availableCopies > 0
                  ? 'bg-emerald-500/90 text-white'
                  : 'bg-red-500/90 text-white'
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${book.availableCopies > 0 ? 'bg-emerald-200' : 'bg-red-200'}`} />
              {book.availableCopies > 0 ? `${book.availableCopies} Available` : 'Checked Out'}
            </span>
          </div>

          {/* Rating overlay (bottom-left) */}
          {Number(book.averageRating) > 0 && (
            <div className="absolute bottom-2 left-2">
              <span className="inline-flex items-center gap-1 rounded-full bg-black/60 px-2 py-0.5 text-xs font-semibold text-white backdrop-blur-sm">
                <StarSolid className="h-3 w-3 text-amber-400" />
                {Number(book.averageRating).toFixed(1)}
              </span>
            </div>
          )}
        </div>

        {/* Book info */}
        <div className="p-3.5">
          <h3 className="font-semibold text-nova-text text-sm leading-snug line-clamp-2 group-hover:text-primary-600 transition-colors">
            {book.title}
          </h3>
          <p className="mt-1 text-xs text-nova-text-muted truncate">
            By {book.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ') || 'Unknown Author'}
          </p>

          {/* Format badges row */}
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
            {/* Physical book format */}
            <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-semibold border ${
              book.availableCopies > 0
                ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400'
                : 'border-gray-200 bg-gray-50 text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400'
            }`}>
              <BookOpenIcon className="h-3 w-3" />
              Book
            </span>
            {/* E-Book format indicator (dynamic) */}
            {book.hasEbook && (
              <span className="inline-flex items-center gap-1 rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                <DocumentTextIcon className="h-3 w-3" />
                E-Book
              </span>
            )}
            {/* Audiobook format indicator (dynamic) */}
            {book.hasAudiobook && (
              <span className="inline-flex items-center gap-1 rounded-md border border-violet-200 bg-violet-50 px-2 py-0.5 text-[10px] font-semibold text-violet-700 dark:border-violet-800 dark:bg-violet-900/20 dark:text-violet-400">
                <MusicalNoteIcon className="h-3 w-3" />
                Audio
              </span>
            )}
            {/* Language */}
            {book.language && book.language !== 'en' && (
              <span className="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-gray-50 px-2 py-0.5 text-[10px] font-semibold text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400">
                <GlobeAltIcon className="h-3 w-3" />
                {book.language.toUpperCase()}
              </span>
            )}
          </div>

          {/* Categories */}
          {book.categories?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {book.categories.slice(0, 2).map((c: any) => (
                <span key={c.id} className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                  {c.name}
                </span>
              ))}
            </div>
          )}

          {/* Description preview */}
          {book.description && (
            <p className="mt-2 text-xs text-nova-text-secondary line-clamp-2 leading-relaxed">
              {book.description}
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}

/* ═══════════════════════════════════════════════════════════
   BookListCard — Horizontal layout with rich details
   ═══════════════════════════════════════════════════════════ */

function BookListCard({ book }: { book: any }) {
  return (
    <Link to={`/catalog/${book.id}`} className="group block">
      <div className="flex gap-5 rounded-xl border border-nova-border bg-nova-surface p-4 shadow-sm transition-all duration-200 hover:shadow-md hover:border-primary-300 dark:hover:border-primary-700">
        {/* Cover */}
        <div className="h-36 w-24 flex-shrink-0 overflow-hidden rounded-lg bg-gray-100 shadow-sm dark:bg-gray-800">
          {book.coverImageUrl ? (
            <img
              src={book.coverImageUrl}
              alt={book.title}
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
            />
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-1 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900">
              <BookOpenIcon className="h-8 w-8 text-gray-300 dark:text-gray-600" />
            </div>
          )}
        </div>

        {/* Info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="font-semibold text-nova-text text-base leading-snug group-hover:text-primary-600 transition-colors line-clamp-1">
                {book.title}
              </h3>
              <p className="mt-0.5 text-sm text-nova-text-muted">
                By {book.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ') || 'Unknown Author'}
              </p>
            </div>

            {/* Availability badge */}
            <span
              className={`flex-shrink-0 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
                book.availableCopies > 0
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800'
                  : 'bg-red-50 text-red-700 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800'
              }`}
            >
              {book.availableCopies > 0 ? (
                <><CheckCircleIcon className="h-3.5 w-3.5" /> {book.availableCopies} Available</>
              ) : (
                <><XCircleIcon className="h-3.5 w-3.5" /> Checked Out</>
              )}
            </span>
          </div>

          {/* Description */}
          {book.description && (
            <p className="mt-2 text-sm text-nova-text-secondary line-clamp-2 leading-relaxed">
              {book.description}
            </p>
          )}

          {/* Bottom row: rating + formats + categories */}
          <div className="mt-3 flex flex-wrap items-center gap-3">
            {/* Rating */}
            {Number(book.averageRating) > 0 && (
              <span className="inline-flex items-center gap-1 text-sm">
                <StarSolid className="h-4 w-4 text-amber-400" />
                <span className="font-semibold text-nova-text">{Number(book.averageRating).toFixed(1)}</span>
                {book.ratingCount > 0 && (
                  <span className="text-xs text-nova-text-muted">({book.ratingCount})</span>
                )}
              </span>
            )}

            {/* Divider */}
            {Number(book.averageRating) > 0 && (
              <span className="h-4 w-px bg-gray-200 dark:bg-gray-700" />
            )}

            {/* Format badges */}
            <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-semibold border ${
              book.availableCopies > 0
                ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400'
                : 'border-gray-200 bg-gray-50 text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400'
            }`}>
              <BookOpenIcon className="h-3 w-3" />
              Book
            </span>
            {book.hasEbook && (
              <span className="inline-flex items-center gap-1 rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                <DocumentTextIcon className="h-3 w-3" />
                E-Book
              </span>
            )}
            {book.hasAudiobook && (
              <span className="inline-flex items-center gap-1 rounded-md border border-violet-200 bg-violet-50 px-2 py-0.5 text-[10px] font-semibold text-violet-700 dark:border-violet-800 dark:bg-violet-900/20 dark:text-violet-400">
                <MusicalNoteIcon className="h-3 w-3" />
                Audio
              </span>
            )}

            {/* Categories */}
            {book.categories?.slice(0, 3).map((c: any) => (
              <span key={c.id} className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                {c.name}
              </span>
            ))}

            {/* Borrows count */}
            {book.totalBorrows > 0 && (
              <>
                <span className="h-4 w-px bg-gray-200 dark:bg-gray-700" />
                <span className="text-xs text-nova-text-muted">
                  {book.totalBorrows} borrow{book.totalBorrows !== 1 ? 's' : ''}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

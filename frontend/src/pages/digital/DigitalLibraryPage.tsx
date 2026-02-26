/**
 * DigitalLibraryPage — premium digital library experience.
 *
 * Features:
 * - "Continue Reading/Listening" hero carousel for in-progress items
 * - Library stats banner (total books, hours read, finished)
 * - Tabbed view: All Collection | E-Books | Audiobooks | Favorites | History
 * - Rich book cards with cover art, progress ring, type badge, time spent
 * - Filter by status (in-progress, finished, new)
 * - Sort (recently accessed, title, progress)
 */

import { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  BookOpenIcon,
  HeartIcon,
  ClockIcon,
  SpeakerWaveIcon,
  PlayIcon,
  CheckCircleIcon,
  FunnelIcon,
  Squares2X2Icon,
  ListBulletIcon,
  ArrowRightIcon,
  MusicalNoteIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import {
  HeartIcon as HeartSolidIcon,
  PlayIcon as PlaySolidIcon,
} from '@heroicons/react/24/solid';
import { useDocumentTitle } from '@/hooks';
import { MY_LIBRARY, MY_READING_SESSIONS, ALL_DIGITAL_ASSETS } from '@/graphql/queries/digital';
import { TOGGLE_FAVORITE } from '@/graphql/mutations/digital';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { Tabs } from '@/components/ui/Tabs';
import { cn, extractGqlError, timeAgo } from '@/lib/utils';

/* ─── helpers ──────────────────────────────── */

function formatDuration(seconds: number): string {
  if (!seconds) return '0m';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function isEbook(item: any): boolean {
  const type = item.digitalAsset?.assetType ?? item.assetType ?? '';
  return type.startsWith('EBOOK') || type === 'EBOOK_PDF' || type === 'EBOOK_EPUB';
}

function isAudiobook(item: any): boolean {
  return (item.digitalAsset?.assetType ?? item.assetType ?? '') === 'AUDIOBOOK';
}

type SortOption = 'recent' | 'title' | 'progress';

/* ─── sub-components ───────────────────────── */

function StatCard({ icon, label, value, color }: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className={cn('flex h-10 w-10 items-center justify-center rounded-xl', color)}>
        {icon}
      </div>
      <div>
        <p className="text-lg font-bold text-nova-text">{value}</p>
        <p className="text-xs text-nova-text-muted">{label}</p>
      </div>
    </div>
  );
}

/** Circular progress ring */
function ProgressRing({ progress, size = 48, strokeWidth = 3 }: { progress: number; size?: number; strokeWidth?: number }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress / 100) * circumference;
  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        className="text-gray-200 dark:text-gray-700"
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        className="text-primary-600 transition-all duration-700"
      />
    </svg>
  );
}

/** Premium book card with cover, progress, and metadata */
function LibraryBookCard({
  item,
  onToggleFavorite,
  viewMode,
}: {
  item: any;
  onToggleFavorite: (assetId: string) => void;
  viewMode: 'grid' | 'list';
}) {
  const asset = item.digitalAsset ?? item;
  const book = asset?.book;
  const isAudio = isAudiobook(item);
  const progress = item.overallProgress ?? 0;
  const finished = item.isFinished;
  const linkTo = isAudio ? `/listen/${asset.id}` : `/reader/${asset.id}`;

  if (viewMode === 'list') {
    return (
      <Card hoverable padding="sm">
        <div className="flex items-center gap-4">
          {/* Cover */}
          <Link to={linkTo} className="relative flex-shrink-0">
            <div className="h-16 w-12 overflow-hidden rounded-lg bg-gray-100 dark:bg-gray-800">
              {book?.coverImageUrl ? (
                <img src={book.coverImageUrl} alt={book.title} className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center">
                  {isAudio
                    ? <MusicalNoteIcon className="h-5 w-5 text-gray-300" />
                    : <DocumentTextIcon className="h-5 w-5 text-gray-300" />}
                </div>
              )}
            </div>
            {/* Type indicator */}
            <div className={cn(
              'absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full text-white shadow-sm',
              isAudio ? 'bg-violet-500' : 'bg-primary-500',
            )}>
              {isAudio ? <SpeakerWaveIcon className="h-3 w-3" /> : <BookOpenIcon className="h-3 w-3" />}
            </div>
          </Link>

          <div className="min-w-0 flex-1">
            <Link to={linkTo} className="text-sm font-semibold text-nova-text hover:text-primary-600 line-clamp-1">
              {book?.title ?? 'Untitled'}
            </Link>
            <p className="text-xs text-nova-text-muted line-clamp-1">
              {book?.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ')}
            </p>
            <div className="mt-1.5 flex items-center gap-3">
              <ProgressBar value={progress} max={100} size="sm" className="flex-1" />
              <span className="text-[10px] font-semibold text-nova-text-muted">{Math.round(progress)}%</span>
            </div>
          </div>

          <div className="flex flex-col items-end gap-1">
            {finished && <Badge variant="success" size="xs">Finished</Badge>}
            {item.totalTimeSeconds > 0 && (
              <span className="text-[10px] text-nova-text-muted">{formatDuration(item.totalTimeSeconds)}</span>
            )}
          </div>

          <button
            onClick={() => onToggleFavorite(asset.id)}
            className="p-1 text-nova-text-muted transition-colors hover:text-red-500"
          >
            {item.isFavorite
              ? <HeartSolidIcon className="h-4 w-4 text-red-500" />
              : <HeartIcon className="h-4 w-4" />}
          </button>
        </div>
      </Card>
    );
  }

  // Grid card
  return (
    <Card hoverable padding="none" className="overflow-hidden group">
      {/* Cover area */}
      <Link to={linkTo} className="relative block">
        <div className="aspect-[3/4] overflow-hidden bg-gray-100 dark:bg-gray-800">
          {book?.coverImageUrl ? (
            <img
              src={book.coverImageUrl}
              alt={book.title}
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full items-center justify-center bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900/30 dark:to-accent-900/30">
              {isAudio
                ? <MusicalNoteIcon className="h-12 w-12 text-primary-300" />
                : <DocumentTextIcon className="h-12 w-12 text-primary-300" />}
            </div>
          )}
        </div>

        {/* Hover overlay with play button */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/30 transition-colors">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/90 text-primary-600 opacity-0 group-hover:opacity-100 transition-opacity shadow-lg">
            <PlaySolidIcon className="h-6 w-6 ml-0.5" />
          </div>
        </div>

        {/* Type badge */}
        <div className="absolute top-2 left-2">
          <Badge
            variant={isAudio ? 'info' : 'primary'}
            size="xs"
          >
            {isAudio ? '🎧 Audio' : '📖 E-Book'}
          </Badge>
        </div>

        {/* Progress ring overlay */}
        {progress > 0 && !finished && (
          <div className="absolute bottom-2 right-2">
            <div className="relative flex items-center justify-center">
              <ProgressRing progress={progress} size={36} strokeWidth={3} />
              <span className="absolute text-[9px] font-bold text-nova-text">{Math.round(progress)}%</span>
            </div>
          </div>
        )}

        {/* Finished checkmark */}
        {finished && (
          <div className="absolute bottom-2 right-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-500 text-white shadow-sm">
              <CheckCircleIcon className="h-5 w-5" />
            </div>
          </div>
        )}
      </Link>

      {/* Info */}
      <div className="p-3">
        <div className="flex items-start justify-between gap-1">
          <div className="min-w-0 flex-1">
            <Link to={linkTo} className="text-sm font-semibold text-nova-text hover:text-primary-600 line-clamp-1">
              {book?.title ?? 'Untitled'}
            </Link>
            <p className="text-xs text-nova-text-muted line-clamp-1">
              {book?.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ')}
            </p>
          </div>
          <button
            onClick={() => onToggleFavorite(asset.id)}
            className="flex-shrink-0 p-0.5 text-nova-text-muted transition-colors hover:text-red-500"
          >
            {item.isFavorite
              ? <HeartSolidIcon className="h-4 w-4 text-red-500" />
              : <HeartIcon className="h-4 w-4" />}
          </button>
        </div>

        <div className="mt-2 flex items-center justify-between text-[10px] text-nova-text-muted">
          {item.totalTimeSeconds > 0 && (
            <span className="flex items-center gap-0.5">
              <ClockIcon className="h-3 w-3" /> {formatDuration(item.totalTimeSeconds)}
            </span>
          )}
          {isAudio && asset?.narrator && (
            <span className="truncate">🎙 {asset.narrator}</span>
          )}
          {!isAudio && asset?.totalPages && (
            <span>{asset.totalPages} pages</span>
          )}
        </div>
      </div>
    </Card>
  );
}

/** Continue Reading/Listening Hero Item */
function ContinueItem({ item }: { item: any }) {
  const asset = item.digitalAsset ?? item;
  const book = asset?.book;
  const isAudio = isAudiobook(item);
  const progress = item.overallProgress ?? 0;
  const linkTo = isAudio ? `/listen/${asset.id}` : `/reader/${asset.id}`;

  return (
    <Link to={linkTo} className="group">
      <div className="relative flex gap-4 rounded-xl border border-nova-border bg-nova-surface p-4 transition-all hover:shadow-lg hover:border-primary-300 dark:hover:border-primary-700">
        {/* Cover */}
        <div className="relative h-24 w-16 flex-shrink-0 overflow-hidden rounded-lg bg-gray-100 dark:bg-gray-800 shadow-md">
          {book?.coverImageUrl ? (
            <img src={book.coverImageUrl} alt={book.title} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center bg-gradient-to-br from-primary-200 to-accent-200 dark:from-primary-800 dark:to-accent-800">
              {isAudio ? <MusicalNoteIcon className="h-6 w-6 text-white/60" /> : <BookOpenIcon className="h-6 w-6 text-white/60" />}
            </div>
          )}
          <div className={cn(
            'absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full text-white shadow-sm',
            isAudio ? 'bg-violet-500' : 'bg-primary-500',
          )}>
            {isAudio ? <SpeakerWaveIcon className="h-3 w-3" /> : <BookOpenIcon className="h-3 w-3" />}
          </div>
        </div>

        {/* Info */}
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-nova-text line-clamp-1 group-hover:text-primary-600 transition-colors">
            {book?.title ?? 'Untitled'}
          </p>
          <p className="text-xs text-nova-text-muted line-clamp-1">
            {book?.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ')}
          </p>
          <div className="mt-3 flex items-center gap-2">
            <ProgressBar value={progress} max={100} size="sm" className="flex-1" />
            <span className="text-xs font-semibold text-primary-600">{Math.round(progress)}%</span>
          </div>
          <p className="mt-1 text-[10px] text-nova-text-muted">
            {item.lastAccessedAt ? `Last read ${timeAgo(item.lastAccessedAt)}` : 'Not started'}
          </p>
        </div>

        {/* Play/Resume button */}
        <div className="flex items-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-600 text-white shadow-md group-hover:bg-primary-700 transition-colors">
            <PlayIcon className="h-5 w-5 ml-0.5" />
          </div>
        </div>
      </div>
    </Link>
  );
}

/* ─── main component ───────────────────────── */

export default function DigitalLibraryPage() {
  useDocumentTitle('Nova Digital Library');

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<SortOption>('title');
  const [showFilter, setShowFilter] = useState(false);
  const [statusFilter, setStatusFilter] = useState<'all' | 'in-progress' | 'finished' | 'new'>('all');

  /* Fetch ALL available digital assets (public collection) */
  const { data: allData, loading: allLoading } = useQuery(ALL_DIGITAL_ASSETS, {
    fetchPolicy: 'cache-and-network',
  });

  /* Fetch user's personal library entries (for progress, favorites, etc.) */
  const { data: libData, loading: libLoading, refetch: refetchLib } = useQuery(MY_LIBRARY, {
    fetchPolicy: 'cache-and-network',
  });

  const { data: sessData, loading: sessLoading } = useQuery(MY_READING_SESSIONS, {
    variables: { limit: 30 },
  });

  const allAssets: any[] = (allData?.allDigitalAssets ?? []).filter(Boolean);
  const library: any[] = (libData?.myLibrary ?? []).filter(Boolean);
  const sessions: any[] = (sessData?.myReadingSessions ?? []).filter(Boolean);

  /* Build a lookup map: asset ID -> UserLibrary entry (for progress/fav) */
  const libMap = useMemo(() => {
    const map: Record<string, any> = {};
    for (const entry of library) {
      if (entry.digitalAsset?.id) map[entry.digitalAsset.id] = entry;
    }
    return map;
  }, [library]);

  /* Merge: enrich each digital asset with the user's personal progress data */
  const enrichedAssets = useMemo(() =>
    allAssets.map((asset: any) => {
      const userEntry = libMap[asset.id];
      return {
        /* the raw asset acts as "digitalAsset" to keep cards working */
        digitalAsset: asset,
        /* overlay personal data if available */
        overallProgress: userEntry?.overallProgress ?? 0,
        totalTimeSeconds: userEntry?.totalTimeSeconds ?? 0,
        isFinished: userEntry?.isFinished ?? false,
        isFavorite: userEntry?.isFavorite ?? false,
        lastAccessedAt: userEntry?.lastAccessedAt ?? null,
        id: userEntry?.id ?? asset.id,
        _hasLibEntry: !!userEntry,
      };
    }),
    [allAssets, libMap],
  );

  const [toggleFavorite] = useMutation(TOGGLE_FAVORITE, {
    onCompleted: () => refetchLib(),
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const handleToggleFavorite = (assetId: string) => {
    toggleFavorite({ variables: { digitalAssetId: assetId } });
  };

  /* ─── computed data ─── */
  const continueReading = useMemo(() =>
    enrichedAssets
      .filter((item: any) => item.overallProgress > 0 && !item.isFinished)
      .sort((a: any, b: any) => {
        const dateA = a.lastAccessedAt ? new Date(a.lastAccessedAt).getTime() : 0;
        const dateB = b.lastAccessedAt ? new Date(b.lastAccessedAt).getTime() : 0;
        return dateB - dateA;
      })
      .slice(0, 4),
    [enrichedAssets],
  );

  const ebooks = useMemo(() => enrichedAssets.filter(isEbook), [enrichedAssets]);
  const audiobooks = useMemo(() => enrichedAssets.filter(isAudiobook), [enrichedAssets]);
  const favorites = useMemo(() => enrichedAssets.filter((item: any) => item.isFavorite), [enrichedAssets]);

  const totalTimeSpent = useMemo(
    () => enrichedAssets.reduce((sum: number, item: any) => sum + (item.totalTimeSeconds ?? 0), 0),
    [enrichedAssets],
  );
  const finishedCount = useMemo(
    () => enrichedAssets.filter((item: any) => item.isFinished).length,
    [enrichedAssets],
  );

  /* ─── filter + sort logic ─── */
  const filterAndSort = useCallback((items: any[]): any[] => {
    let filtered = items;
    if (statusFilter === 'in-progress') {
      filtered = items.filter((i: any) => i.overallProgress > 0 && !i.isFinished);
    } else if (statusFilter === 'finished') {
      filtered = items.filter((i: any) => i.isFinished);
    } else if (statusFilter === 'new') {
      filtered = items.filter((i: any) => !i.overallProgress || i.overallProgress === 0);
    }

    return [...filtered].sort((a: any, b: any) => {
      if (sortBy === 'title') {
        return (a.digitalAsset?.book?.title ?? '').localeCompare(b.digitalAsset?.book?.title ?? '');
      }
      if (sortBy === 'progress') {
        return (b.overallProgress ?? 0) - (a.overallProgress ?? 0);
      }
      // recent
      const dateA = a.lastAccessedAt ? new Date(a.lastAccessedAt).getTime() : 0;
      const dateB = b.lastAccessedAt ? new Date(b.lastAccessedAt).getTime() : 0;
      return dateB - dateA;
    });
  }, [statusFilter, sortBy]);

  if (allLoading && libLoading) return <LoadingOverlay />;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ─── Header ─── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">Nova Digital Library</h1>
          <p className="text-sm text-nova-text-secondary">
            Browse and read e-books and audiobooks provided by your library
          </p>
        </div>
        <Link to="/catalog">
          <Button variant="outline" size="sm" rightIcon={<ArrowRightIcon className="h-3.5 w-3.5" />}>
            Browse Catalog
          </Button>
        </Link>
      </div>

      {/* ─── Stats Banner ─── */}
      {enrichedAssets.length > 0 && (
        <Card className="bg-gradient-to-r from-primary-50 via-white to-accent-50 dark:from-primary-900/10 dark:via-nova-surface dark:to-accent-900/10">
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
            <StatCard
              icon={<BookOpenIcon className="h-5 w-5 text-primary-600" />}
              label="Available Titles"
              value={enrichedAssets.length}
              color="bg-primary-100 dark:bg-primary-900/30"
            />
            <StatCard
              icon={<MusicalNoteIcon className="h-5 w-5 text-violet-600" />}
              label="Audiobooks"
              value={audiobooks.length}
              color="bg-violet-100 dark:bg-violet-900/30"
            />
            <StatCard
              icon={<ClockIcon className="h-5 w-5 text-amber-600" />}
              label="Time Spent"
              value={formatDuration(totalTimeSpent)}
              color="bg-amber-100 dark:bg-amber-900/30"
            />
            <StatCard
              icon={<CheckCircleIcon className="h-5 w-5 text-green-600" />}
              label="Finished"
              value={finishedCount}
              color="bg-green-100 dark:bg-green-900/30"
            />
          </div>
        </Card>
      )}

      {/* ─── Continue Reading/Listening ─── */}
      {continueReading.length > 0 && (
        <div>
          <h2 className="mb-3 text-lg font-semibold text-nova-text flex items-center gap-2">
            <PlayIcon className="h-5 w-5 text-primary-600" />
            Continue Where You Left Off
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {continueReading.map((item: any) => (
              <ContinueItem key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}

      {/* ─── Library Empty State ─── */}
      {enrichedAssets.length === 0 ? (
        <EmptyState
          icon={<BookOpenIcon />}
          title="No digital content available yet"
          description="The library hasn't uploaded any e-books or audiobooks yet. Check back soon!"
        />
      ) : (
        <>
          {/* ─── Controls Bar ─── */}
          <div className="flex flex-wrap items-center gap-3">
            {/* View toggle */}
            <div className="flex rounded-lg border border-nova-border bg-nova-surface p-0.5">
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  'rounded-md px-2 py-1 transition-colors',
                  viewMode === 'grid'
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                    : 'text-nova-text-muted hover:text-nova-text',
                )}
              >
                <Squares2X2Icon className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'rounded-md px-2 py-1 transition-colors',
                  viewMode === 'list'
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                    : 'text-nova-text-muted hover:text-nova-text',
                )}
              >
                <ListBulletIcon className="h-4 w-4" />
              </button>
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="rounded-lg border border-nova-border bg-nova-surface px-3 py-1.5 text-xs text-nova-text"
            >
              <option value="recent">Recently Accessed</option>
              <option value="title">Title A-Z</option>
              <option value="progress">Progress</option>
            </select>

            {/* Filter toggle */}
            <button
              onClick={() => setShowFilter(!showFilter)}
              className={cn(
                'flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
                showFilter || statusFilter !== 'all'
                  ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                  : 'border-nova-border text-nova-text-secondary hover:bg-nova-surface-hover',
              )}
            >
              <FunnelIcon className="h-3.5 w-3.5" />
              Filter
            </button>

            {/* Filter chips */}
            {showFilter && (
              <div className="flex gap-1.5">
                {(['all', 'in-progress', 'finished', 'new'] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setStatusFilter(f)}
                    className={cn(
                      'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                      f === statusFilter
                        ? 'bg-primary-600 text-white'
                        : 'bg-nova-surface-hover text-nova-text-secondary hover:text-nova-text',
                    )}
                  >
                    {f === 'all' ? 'All' : f === 'in-progress' ? 'In Progress' : f === 'finished' ? 'Finished' : 'New'}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* ─── Tabbed Content ─── */}
          <Tabs
            variant="pills"
            tabs={[
              {
                label: 'All',
                icon: <Squares2X2Icon className="h-4 w-4" />,
                badge: enrichedAssets.length,
                content: (
                  <div className={viewMode === 'grid'
                    ? 'grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
                    : 'space-y-2'
                  }>
                    {filterAndSort(enrichedAssets).map((item: any) => (
                      <LibraryBookCard
                        key={item.digitalAsset?.id ?? item.id}
                        item={item}
                        onToggleFavorite={handleToggleFavorite}
                        viewMode={viewMode}
                      />
                    ))}
                  </div>
                ),
              },
              {
                label: 'E-Books',
                icon: <DocumentTextIcon className="h-4 w-4" />,
                badge: ebooks.length,
                content: ebooks.length === 0 ? (
                  <EmptyState
                    icon={<DocumentTextIcon />}
                    title="No e-books yet"
                    description="Browse the catalog to find e-books."
                  />
                ) : (
                  <div className={viewMode === 'grid'
                    ? 'grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
                    : 'space-y-2'
                  }>
                    {filterAndSort(ebooks).map((item: any) => (
                      <LibraryBookCard
                        key={item.id}
                        item={item}
                        onToggleFavorite={handleToggleFavorite}
                        viewMode={viewMode}
                      />
                    ))}
                  </div>
                ),
              },
              {
                label: 'Audiobooks',
                icon: <MusicalNoteIcon className="h-4 w-4" />,
                badge: audiobooks.length,
                content: audiobooks.length === 0 ? (
                  <EmptyState
                    icon={<SpeakerWaveIcon />}
                    title="No audiobooks yet"
                    description="Browse the catalog to find audiobooks."
                  />
                ) : (
                  <div className={viewMode === 'grid'
                    ? 'grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
                    : 'space-y-2'
                  }>
                    {filterAndSort(audiobooks).map((item: any) => (
                      <LibraryBookCard
                        key={item.id}
                        item={item}
                        onToggleFavorite={handleToggleFavorite}
                        viewMode={viewMode}
                      />
                    ))}
                  </div>
                ),
              },
              {
                label: 'Favorites',
                icon: <HeartIcon className="h-4 w-4" />,
                badge: favorites.length,
                content: favorites.length === 0 ? (
                  <EmptyState
                    icon={<HeartIcon />}
                    title="No favorites yet"
                    description="Tap the heart icon on any book to add it to favorites."
                  />
                ) : (
                  <div className={viewMode === 'grid'
                    ? 'grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
                    : 'space-y-2'
                  }>
                    {filterAndSort(favorites).map((item: any) => (
                      <LibraryBookCard
                        key={item.id}
                        item={item}
                        onToggleFavorite={handleToggleFavorite}
                        viewMode={viewMode}
                      />
                    ))}
                  </div>
                ),
              },
              {
                label: 'Activity',
                icon: <ClockIcon className="h-4 w-4" />,
                badge: sessions.length,
                content: sessLoading ? (
                  <LoadingOverlay />
                ) : sessions.length === 0 ? (
                  <EmptyState
                    icon={<ClockIcon />}
                    title="No reading sessions yet"
                    description="Start reading or listening to track your sessions."
                  />
                ) : (
                  <div className="space-y-2">
                    {sessions.map((session: any) => (
                      <Card key={session.id} padding="sm">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              'flex h-8 w-8 items-center justify-center rounded-lg',
                              session.sessionType === 'LISTENING'
                                ? 'bg-violet-100 text-violet-600 dark:bg-violet-900/30'
                                : 'bg-primary-100 text-primary-600 dark:bg-primary-900/30',
                            )}>
                              {session.sessionType === 'LISTENING'
                                ? <SpeakerWaveIcon className="h-4 w-4" />
                                : <BookOpenIcon className="h-4 w-4" />}
                            </div>
                            <div>
                              <p className="text-sm font-medium text-nova-text">
                                {session.digitalAsset?.book?.title ?? 'Unknown'}
                              </p>
                              <p className="text-xs text-nova-text-muted">
                                {timeAgo(session.startedAt)}
                                {session.durationSeconds && ` · ${formatDuration(session.durationSeconds)}`}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {session.progressPercent > 0 && (
                              <span className="text-xs font-medium text-nova-text-secondary">
                                {Math.round(session.progressPercent)}%
                              </span>
                            )}
                            <Badge
                              variant={session.endedAt ? 'success' : 'warning'}
                              size="xs"
                              dot
                            >
                              {session.endedAt ? 'Done' : 'Active'}
                            </Badge>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                ),
              },
            ]}
          />
        </>
      )}
    </div>
  );
}

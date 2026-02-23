/**
 * DashboardPage — premium landing page with hero stats, streak flame,
 * continue-reading/listening widget, KP snapshot, recent borrows,
 * trending books, and AI recommendations.
 */

import { useMemo } from 'react';
import { useQuery } from '@apollo/client';
import { Link } from 'react-router-dom';
import {
  BookOpenIcon,
  ClockIcon,
  TrophyIcon,
  SparklesIcon,
  ArrowTrendingUpIcon,
  ArrowRightIcon,
  FireIcon,
  PlayIcon,
  MusicalNoteIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { useAuthStore } from '@/stores/authStore';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingOverlay, SkeletonCard } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Button } from '@/components/ui/Button';
import { MY_BORROWS } from '@/graphql/queries/circulation';
import { MY_RECOMMENDATIONS } from '@/graphql/queries/intelligence';
import { MY_ENGAGEMENT, MY_DAILY_ACTIVITY } from '@/graphql/queries/engagement';
import { MY_LIBRARY } from '@/graphql/queries/digital';
import { TRENDING_BOOKS } from '@/graphql/queries/intelligence';
import { cn, kpLevelName, formatDate, formatNumber } from '@/lib/utils';

/* ─── helpers ────────────────────────────────── */

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function formatMinutes(sec: number): string {
  const mins = Math.round(sec / 60);
  if (mins < 60) return `${mins}m`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export default function DashboardPage() {
  useDocumentTitle('Dashboard');
  const user = useAuthStore((s) => s.user);

  const { data: borrowsData, loading: borrowsLoading } = useQuery(MY_BORROWS, {
    variables: { limit: 5 },
  });
  const { data: recsData, loading: recsLoading } = useQuery(MY_RECOMMENDATIONS, {
    variables: { limit: 6 },
  });
  const { data: engData } = useQuery(MY_ENGAGEMENT);
  const { data: trendingData } = useQuery(TRENDING_BOOKS, {
    variables: { period: 'WEEKLY', limit: 5 },
  });
  const { data: libData } = useQuery(MY_LIBRARY);
  const { data: actData } = useQuery(MY_DAILY_ACTIVITY, { variables: { days: 7 } });

  const borrows = borrowsData?.myBorrows ?? [];
  const recommendations = recsData?.myRecommendations ?? [];
  const engagement = engData?.myEngagement;
  const trending = trendingData?.trendingBooks ?? [];
  const library = libData?.myLibrary ?? [];
  const weekActivity = actData?.myDailyActivity ?? [];

  // Continue reading/listening — in-progress items sorted by last accessed
  const continueItems = useMemo(() => {
    return library
      .filter((e: any) => e.overallProgress > 0 && !e.isFinished)
      .sort((a: any, b: any) => {
        const da = a.lastAccessedAt ? new Date(a.lastAccessedAt).getTime() : 0;
        const db = b.lastAccessedAt ? new Date(b.lastAccessedAt).getTime() : 0;
        return db - da;
      })
      .slice(0, 3);
  }, [library]);

  // Weekly KP total
  const weekKp = useMemo(
    () => weekActivity.reduce((s: number, a: any) => s + (a.kpEarned ?? 0), 0),
    [weekActivity],
  );
  const weekReadMins = useMemo(
    () => weekActivity.reduce((s: number, a: any) => s + (a.readingMinutes ?? 0), 0),
    [weekActivity],
  );

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ─── Welcome Hero ─── */}
      <div className="rounded-2xl bg-gradient-to-br from-primary-600 via-primary-700 to-accent-700 p-6 text-white shadow-lg sm:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-primary-200 text-sm font-medium">{getGreeting()},</p>
            <h1 className="text-2xl font-bold sm:text-3xl">
              {user?.firstName ?? 'Reader'} {user?.lastName ?? ''}
            </h1>
            <p className="mt-1 text-primary-100/80 text-sm">
              Here&apos;s your library activity at a glance
            </p>
          </div>

          {/* Quick streak badge */}
          {engagement && (
            <div className="flex items-center gap-4">
              {engagement.currentStreak > 0 && (
                <div className="flex items-center gap-2 rounded-xl bg-white/15 backdrop-blur-sm px-4 py-2">
                  <FireIcon className="h-6 w-6 text-orange-300" />
                  <div>
                    <p className="text-lg font-black leading-none">{engagement.currentStreak}</p>
                    <p className="text-[10px] text-primary-200">day streak</p>
                  </div>
                </div>
              )}
              <Link to="/kp-center">
                <div className="flex items-center gap-2 rounded-xl bg-white/15 backdrop-blur-sm px-4 py-2 hover:bg-white/25 transition-colors cursor-pointer">
                  <TrophyIcon className="h-6 w-6 text-amber-300" />
                  <div>
                    <p className="text-lg font-black leading-none">{formatNumber(engagement.totalKp)}</p>
                    <p className="text-[10px] text-primary-200">KP · L{engagement.level}</p>
                  </div>
                </div>
              </Link>
            </div>
          )}
        </div>

        {/* Mini stats row inside hero */}
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <MiniStat label="Active Borrows" value={borrows.filter((b: any) => b.status === 'ACTIVE').length} />
          <MiniStat label="Digital Books" value={library.length} />
          <MiniStat label="KP This Week" value={`+${weekKp}`} />
          <MiniStat label="Reading Time" value={`${weekReadMins}m`} />
        </div>
      </div>

      {/* ─── Continue Reading/Listening ─── */}
      {continueItems.length > 0 && (
        <div>
          <h2 className="mb-3 text-lg font-semibold text-nova-text flex items-center gap-2">
            <PlayIcon className="h-5 w-5 text-primary-500" />
            Continue Where You Left Off
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {continueItems.map((entry: any) => {
              const asset = entry.digitalAsset;
              const book = asset?.book;
              const isAudio = asset?.assetType === 'AUDIOBOOK';
              const link = isAudio ? `/listen/${asset.id}` : `/reader/${asset.id}`;
              return (
                <Link key={entry.id} to={link}>
                  <Card hoverable padding="sm">
                    <div className="flex gap-3">
                      {/* Cover */}
                      {book?.coverImageUrl ? (
                        <div className="relative flex-shrink-0">
                          <img
                            src={book.coverImageUrl}
                            alt={book.title}
                            className="h-20 w-14 rounded-lg object-cover shadow"
                          />
                          <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-black/40 opacity-0 hover:opacity-100 transition-opacity">
                            {isAudio ? (
                              <MusicalNoteIcon className="h-6 w-6 text-white" />
                            ) : (
                              <BookOpenIcon className="h-6 w-6 text-white" />
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="flex h-20 w-14 items-center justify-center rounded-lg bg-primary-50 dark:bg-primary-900/20 flex-shrink-0">
                          {isAudio ? (
                            <MusicalNoteIcon className="h-6 w-6 text-primary-400" />
                          ) : (
                            <BookOpenIcon className="h-6 w-6 text-primary-400" />
                          )}
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-nova-text">{book?.title}</p>
                        <p className="text-xs text-nova-text-muted truncate">
                          {book?.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ')}
                        </p>
                        <div className="mt-2 flex items-center gap-2">
                          <ProgressBar
                            value={entry.overallProgress}
                            max={100}
                            size="sm"
                            color={isAudio ? 'accent' : 'primary'}
                            className="flex-1"
                          />
                          <span className="text-[10px] font-semibold text-nova-text-muted">
                            {Math.round(entry.overallProgress)}%
                          </span>
                        </div>
                        <div className="mt-1 flex items-center gap-2">
                          <Badge variant={isAudio ? 'info' : 'primary'} size="xs">
                            {isAudio ? '🎧 Audio' : '📖 E-Book'}
                          </Badge>
                          {entry.totalTimeSeconds > 0 && (
                            <span className="text-[10px] text-nova-text-muted">
                              {formatMinutes(entry.totalTimeSeconds)} spent
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* ─── Stats Row ─── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<BookOpenIcon className="h-5 w-5" />}
          label="Active Borrows"
          value={borrows.filter((b: any) => b.status === 'ACTIVE').length}
          color="primary"
        />
        <StatCard
          icon={<ClockIcon className="h-5 w-5" />}
          label="Overdue"
          value={borrows.filter((b: any) => b.status === 'OVERDUE').length}
          color="danger"
          alert={borrows.filter((b: any) => b.status === 'OVERDUE').length > 0}
        />
        <StatCard
          icon={<TrophyIcon className="h-5 w-5" />}
          label="Knowledge Points"
          value={formatNumber(engagement?.totalKp ?? 0)}
          color="accent"
          sub={engagement ? `Level ${engagement.level}` : undefined}
        />
        <StatCard
          icon={<ArrowTrendingUpIcon className="h-5 w-5" />}
          label="KP Level"
          value={kpLevelName(engagement?.level ?? 1)}
          color="success"
        />
      </div>

      {/* ─── KP Progress + Quick Actions ─── */}
      {engagement && (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader
              title="Knowledge Points Progress"
              description={`Level ${engagement.level}: ${kpLevelName(engagement.level)}`}
              action={
                <Link to="/kp-center">
                  <Button variant="ghost" size="xs" rightIcon={<ArrowRightIcon className="h-3.5 w-3.5" />}>
                    KP Center
                  </Button>
                </Link>
              }
            />
            <div className="mt-4 space-y-3">
              <ProgressBar
                value={engagement.totalKp % 1000}
                max={1000}
                showValue
                label={`${formatNumber(engagement.totalKp)} KP`}
                color="accent"
              />
              <div className="flex items-center gap-4 text-xs text-nova-text-muted">
                {engagement.currentStreak > 0 && (
                  <span className="flex items-center gap-1">
                    <FireIcon className="h-3.5 w-3.5 text-orange-500" />
                    {engagement.currentStreak} day streak
                    {engagement.streakMultiplier > 1 && (
                      <Badge variant="warning" size="xs">{engagement.streakMultiplier}x</Badge>
                    )}
                  </span>
                )}
                {engagement.rank && (
                  <span className="flex items-center gap-1">
                    <ChartBarIcon className="h-3.5 w-3.5" />
                    Rank #{engagement.rank}
                  </span>
                )}
              </div>
            </div>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader title="Quick Actions" />
            <div className="mt-3 grid grid-cols-2 gap-2">
              {[
                { label: 'My Library', icon: BookOpenIcon, to: '/library', color: 'bg-primary-100 text-primary-600 dark:bg-primary-900/30' },
                { label: 'KP Center', icon: TrophyIcon, to: '/kp-center', color: 'bg-amber-100 text-amber-600 dark:bg-amber-900/30' },
                { label: 'Achievements', icon: SparklesIcon, to: '/achievements', color: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30' },
                { label: 'Insights', icon: ChartBarIcon, to: '/insights', color: 'bg-green-100 text-green-600 dark:bg-green-900/30' },
              ].map((action) => (
                <Link key={action.to} to={action.to}>
                  <div className="flex items-center gap-2 rounded-xl p-3 hover:bg-nova-surface-hover transition-colors cursor-pointer">
                    <div className={cn('flex h-8 w-8 items-center justify-center rounded-lg', action.color)}>
                      <action.icon className="h-4 w-4" />
                    </div>
                    <span className="text-xs font-medium text-nova-text">{action.label}</span>
                  </div>
                </Link>
              ))}
            </div>
          </Card>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* ─── Recent Borrows ─── */}
        <Card>
          <CardHeader
            title="Recent Borrows"
            action={
              <Link to="/borrows">
                <Button variant="ghost" size="xs" rightIcon={<ArrowRightIcon className="h-3.5 w-3.5" />}>
                  View all
                </Button>
              </Link>
            }
          />
          <div className="mt-4 divide-y divide-nova-border">
            {borrowsLoading ? (
              <LoadingOverlay />
            ) : borrows.length === 0 ? (
              <EmptyState
                title="No borrows yet"
                description="Browse the catalog and borrow your first book."
                action={
                  <Link to="/catalog">
                    <Button size="sm">Browse Catalog</Button>
                  </Link>
                }
              />
            ) : (
              borrows.slice(0, 5).map((b: any) => (
                <div key={b.id} className="flex items-center justify-between py-3">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-nova-text">
                      {b.bookCopy?.book?.title ?? 'Unknown Book'}
                    </p>
                    <p className="text-xs text-nova-text-muted">
                      Due {formatDate(b.dueDate)}
                    </p>
                  </div>
                  <Badge
                    variant={
                      b.status === 'RETURNED'
                        ? 'success'
                        : b.status === 'OVERDUE'
                          ? 'danger'
                          : 'primary'
                    }
                    size="xs"
                  >
                    {b.status}
                  </Badge>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* ─── Trending Books ─── */}
        <Card>
          <CardHeader
            title="Trending This Week"
            action={
              <Link to="/catalog">
                <Button variant="ghost" size="xs" rightIcon={<ArrowRightIcon className="h-3.5 w-3.5" />}>
                  Catalog
                </Button>
              </Link>
            }
          />
          <div className="mt-4 divide-y divide-nova-border">
            {trending.length === 0 ? (
              <p className="py-6 text-center text-sm text-nova-text-muted">
                No trending data yet
              </p>
            ) : (
              trending.map((item: any, idx: number) => (
                <div key={item.book?.id ?? idx} className="flex items-center gap-3 py-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-50 text-xs font-bold text-primary-600 dark:bg-primary-900/30">
                    {idx + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-nova-text">
                      {item.book?.title ?? 'Unknown'}
                    </p>
                    <p className="text-xs text-nova-text-muted">
                      {item.score ?? 0} points
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* ─── Recommendations ─── */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-nova-text">
            <SparklesIcon className="mr-2 inline h-5 w-5 text-accent-500" />
            Recommended for You
          </h2>
          <Link to="/recommendations">
            <Button variant="ghost" size="xs" rightIcon={<ArrowRightIcon className="h-3.5 w-3.5" />}>
              See all
            </Button>
          </Link>
        </div>
        {recsLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : recommendations.length === 0 ? (
          <EmptyState
            title="No recommendations yet"
            description="Start reading to get personalized suggestions."
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {recommendations.slice(0, 6).map((rec: any) => (
              <Link key={rec.id} to={`/catalog/${rec.book?.id}`}>
                <Card hoverable padding="sm">
                  <div className="flex gap-3">
                    {rec.book?.coverImageUrl ? (
                      <img
                        src={rec.book.coverImageUrl}
                        alt={rec.book.title}
                        className="h-20 w-14 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="flex h-20 w-14 items-center justify-center rounded-lg bg-primary-50 dark:bg-primary-900/20">
                        <BookOpenIcon className="h-6 w-6 text-primary-400" />
                      </div>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-nova-text">
                        {rec.book?.title}
                      </p>
                      <p className="text-xs text-nova-text-muted">
                        {rec.book?.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ') ?? 'Unknown'}
                      </p>
                      <Badge variant="primary" size="xs" className="mt-2">
                        {Math.round((rec.score ?? 0) * 100)}% match
                      </Badge>
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Sub-components ─────────────────────────── */

/** Translucent mini-stat for the hero banner */
function MiniStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl bg-white/10 backdrop-blur-sm px-3 py-2">
      <p className="text-lg font-bold leading-none">{value}</p>
      <p className="mt-0.5 text-[10px] text-primary-200">{label}</p>
    </div>
  );
}

/** Standard stat card */
function StatCard({
  icon,
  label,
  value,
  color,
  alert,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: 'primary' | 'accent' | 'danger' | 'success';
  alert?: boolean;
  sub?: string;
}) {
  const bg = {
    primary: 'bg-primary-50 text-primary-600 dark:bg-primary-900/20',
    accent: 'bg-accent-50 text-accent-600 dark:bg-accent-900/20',
    danger: 'bg-red-50 text-red-600 dark:bg-red-900/20',
    success: 'bg-green-50 text-green-600 dark:bg-green-900/20',
  };

  return (
    <Card className={cn(alert && 'border-red-300 dark:border-red-700')}>
      <div className="flex items-center gap-3">
        <div className={cn('flex h-10 w-10 items-center justify-center rounded-xl', bg[color])}>
          {icon}
        </div>
        <div>
          <p className="text-sm text-nova-text-secondary">{label}</p>
          <p className="text-xl font-bold text-nova-text">{value}</p>
          {sub && <p className="text-[10px] text-nova-text-muted">{sub}</p>}
        </div>
      </div>
    </Card>
  );
}

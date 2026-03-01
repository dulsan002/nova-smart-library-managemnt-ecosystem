/**
 * KnowledgePointsPage — comprehensive gamification & KP dashboard.
 *
 * Features:
 * - Level tier visualization with current level highlight and XP to next level
 * - KP dimension radar/pentagon chart (Explorer, Scholar, Connector, Achiever, Dedicated)
 * - Streak tracker with flame animation and calendar heatmap
 * - Daily activity chart (last 30 days)
 * - Recent KP earning history
 * - Rank & percentile display
 * - Achievement progress summary
 */

import { useMemo } from 'react';
import { useQuery } from '@apollo/client';
import { Link } from 'react-router-dom';
import {
  TrophyIcon,
  FireIcon,
  ArrowTrendingUpIcon,
  SparklesIcon,
  AcademicCapIcon,
  UserGroupIcon,
  StarIcon,
  HeartIcon,
  ChevronRightIcon,
  BookOpenIcon,
  ChartBarIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { MY_ENGAGEMENT, MY_DAILY_ACTIVITY, MY_RANK, MY_ACHIEVEMENTS, ALL_ACHIEVEMENTS } from '@/graphql/queries/engagement';
import { MY_KP_HISTORY } from '@/graphql/queries/governance';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { cn, formatNumber, formatDate } from '@/lib/utils';

/* ─── constants ──────────────────────────────── */

const LEVEL_TIERS = [
  { level: 1, name: 'Novice Reader', kpRequired: 0, color: 'bg-gray-400', textColor: 'text-gray-600', icon: '📖' },
  { level: 2, name: 'Avid Reader', kpRequired: 100, color: 'bg-amber-700', textColor: 'text-amber-700', icon: '🥉' },
  { level: 3, name: 'Scholar', kpRequired: 300, color: 'bg-gray-300', textColor: 'text-gray-500', icon: '🥈' },
  { level: 4, name: 'Bibliophile', kpRequired: 600, color: 'bg-yellow-400', textColor: 'text-yellow-600', icon: '🥇' },
  { level: 5, name: 'Knowledge Keeper', kpRequired: 1000, color: 'bg-cyan-400', textColor: 'text-cyan-600', icon: '💎' },
  { level: 6, name: 'Sage', kpRequired: 1500, color: 'bg-violet-500', textColor: 'text-violet-600', icon: '👑' },
  { level: 7, name: 'Grand Master', kpRequired: 2500, color: 'bg-rose-500', textColor: 'text-rose-600', icon: '🌟' },
];

const KP_DIMENSIONS = [
  { key: 'explorerKp', name: 'Explorer', icon: SparklesIcon, color: 'text-blue-500', bg: 'bg-blue-100 dark:bg-blue-900/30', description: 'Discover new books & genres' },
  { key: 'scholarKp', name: 'Scholar', icon: AcademicCapIcon, color: 'text-purple-500', bg: 'bg-purple-100 dark:bg-purple-900/30', description: 'Deep reading & learning' },
  { key: 'connectorKp', name: 'Connector', icon: UserGroupIcon, color: 'text-green-500', bg: 'bg-green-100 dark:bg-green-900/30', description: 'Reviews & social activity' },
  { key: 'achieverKp', name: 'Achiever', icon: StarIcon, color: 'text-amber-500', bg: 'bg-amber-100 dark:bg-amber-900/30', description: 'Complete goals & milestones' },
  { key: 'dedicatedKp', name: 'Dedicated', icon: HeartIcon, color: 'text-red-500', bg: 'bg-red-100 dark:bg-red-900/30', description: 'Consistency & streaks' },
];

/* ─── sub-components ─────────────────────────── */

/** SVG Pentagon/Radar chart for KP dimensions */
function KPRadarChart({ dimensions }: { dimensions: { name: string; value: number; max: number }[] }) {
  const cx = 120;
  const cy = 120;
  const maxRadius = 90;
  const n = dimensions.length;

  // Compute points for each level ring (25%, 50%, 75%, 100%)
  function getPoint(index: number, radiusPct: number) {
    const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
    const r = maxRadius * radiusPct;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  }

  function ringPath(pct: number) {
    return dimensions
      .map((_, i) => {
        const p = getPoint(i, pct);
        return `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`;
      })
      .join(' ') + ' Z';
  }

  const dataPath = dimensions
    .map((d, i) => {
      const pct = d.max > 0 ? Math.min(d.value / d.max, 1) : 0;
      const p = getPoint(i, pct);
      return `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`;
    })
    .join(' ') + ' Z';

  return (
    <svg viewBox="0 0 240 240" className="h-full w-full">
      {/* Grid rings */}
      {[0.25, 0.5, 0.75, 1].map((pct) => (
        <path
          key={pct}
          d={ringPath(pct)}
          fill="none"
          stroke="currentColor"
          strokeWidth="0.5"
          className="text-gray-200 dark:text-gray-700"
        />
      ))}

      {/* Axis lines */}
      {dimensions.map((_, i) => {
        const p = getPoint(i, 1);
        return (
          <line
            key={i}
            x1={cx}
            y1={cy}
            x2={p.x}
            y2={p.y}
            stroke="currentColor"
            strokeWidth="0.5"
            className="text-gray-200 dark:text-gray-700"
          />
        );
      })}

      {/* Data polygon */}
      <path
        d={dataPath}
        fill="currentColor"
        fillOpacity={0.15}
        stroke="currentColor"
        strokeWidth="2"
        className="text-primary-500"
      />

      {/* Data points */}
      {dimensions.map((d, i) => {
        const pct = d.max > 0 ? Math.min(d.value / d.max, 1) : 0;
        const p = getPoint(i, pct);
        return (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="4"
            fill="currentColor"
            className="text-primary-600"
          />
        );
      })}

      {/* Labels */}
      {dimensions.map((d, i) => {
        const p = getPoint(i, 1.18);
        return (
          <text
            key={i}
            x={p.x}
            y={p.y}
            textAnchor="middle"
            dominantBaseline="central"
            className="fill-current text-nova-text text-[10px] font-semibold"
          >
            {d.name}
          </text>
        );
      })}
    </svg>
  );
}

/** Activity heatmap calendar (last 30 days) */
function ActivityHeatmap({ activities }: { activities: any[] }) {
  const today = new Date();
  const days = Array.from({ length: 30 }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() - (29 - i));
    return d;
  });

  const activityMap = new Map<string, number>();
  activities.forEach((a: any) => {
    if (a.kpEarned) activityMap.set(a.date, a.kpEarned);
  });

  const maxKp = Math.max(1, ...Array.from(activityMap.values()));

  return (
    <div>
      <div className="flex gap-1 flex-wrap">
        {days.map((day) => {
          const key = day.toISOString().slice(0, 10);
          const kp = activityMap.get(key) ?? 0;
          const intensity = kp / maxKp;
          const isToday = key === today.toISOString().slice(0, 10);

          return (
            <div
              key={key}
              className={cn(
                'h-7 w-7 rounded-md transition-colors relative group',
                kp === 0
                  ? 'bg-gray-100 dark:bg-gray-800'
                  : intensity > 0.75
                    ? 'bg-primary-600'
                    : intensity > 0.5
                      ? 'bg-primary-400'
                      : intensity > 0.25
                        ? 'bg-primary-300'
                        : 'bg-primary-200 dark:bg-primary-800',
                isToday && 'ring-2 ring-primary-500 ring-offset-1 dark:ring-offset-nova-bg',
              )}
              title={`${key}: ${kp} KP`}
            >
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block z-10">
                <div className="rounded-lg bg-gray-900 px-2 py-1 text-[10px] text-white whitespace-nowrap shadow-lg">
                  {day.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}: {kp} KP
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex items-center gap-2 text-[10px] text-nova-text-muted">
        <span>Less</span>
        <div className="flex gap-0.5">
          <div className="h-3 w-3 rounded-sm bg-gray-100 dark:bg-gray-800" />
          <div className="h-3 w-3 rounded-sm bg-primary-200 dark:bg-primary-800" />
          <div className="h-3 w-3 rounded-sm bg-primary-300" />
          <div className="h-3 w-3 rounded-sm bg-primary-400" />
          <div className="h-3 w-3 rounded-sm bg-primary-600" />
        </div>
        <span>More</span>
      </div>
    </div>
  );
}

/** Level tier progress visualization */
function LevelTierTrack({ currentLevel, totalKp }: { currentLevel: number; totalKp: number }) {
  return (
    <div className="space-y-3">
      {LEVEL_TIERS.map((tier, idx) => {
        const nextTier = LEVEL_TIERS[idx + 1];
        const isCurrent = tier.level === currentLevel;
        const isAchieved = currentLevel >= tier.level;
        const kpInTier = nextTier
          ? Math.max(0, Math.min(totalKp - tier.kpRequired, nextTier.kpRequired - tier.kpRequired))
          : 0;
        const tierRange = nextTier ? nextTier.kpRequired - tier.kpRequired : 1000;
        const tierProgress = nextTier ? (kpInTier / tierRange) * 100 : 100;

        return (
          <div
            key={tier.level}
            className={cn(
              'flex items-center gap-3 rounded-xl p-3 transition-all',
              isCurrent
                ? 'bg-primary-50 border-2 border-primary-300 shadow-sm dark:bg-primary-900/20 dark:border-primary-700'
                : isAchieved
                  ? 'opacity-70'
                  : 'opacity-40',
            )}
          >
            {/* Tier icon */}
            <div className={cn(
              'flex h-10 w-10 items-center justify-center rounded-xl text-lg',
              isAchieved ? tier.color + ' text-white' : 'bg-gray-200 dark:bg-gray-700',
            )}>
              {tier.icon}
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className={cn('text-sm font-semibold', isCurrent ? 'text-primary-700 dark:text-primary-300' : 'text-nova-text')}>
                  Level {tier.level}: {tier.name}
                </span>
                {isCurrent && (
                  <Badge variant="primary" size="xs">Current</Badge>
                )}
              </div>
              {nextTier && isAchieved && (
                <div className="mt-1 flex items-center gap-2">
                  <ProgressBar
                    value={isCurrent ? tierProgress : 100}
                    max={100}
                    size="sm"
                    color={isCurrent ? 'primary' : 'success'}
                    className="flex-1"
                  />
                  <span className="text-[10px] text-nova-text-muted">
                    {isCurrent
                      ? `${formatNumber(kpInTier)}/${formatNumber(tierRange)} KP`
                      : '✓'}
                  </span>
                </div>
              )}
              {!isAchieved && (
                <p className="text-[10px] text-nova-text-muted mt-0.5">
                  {formatNumber(tier.kpRequired - totalKp)} KP more to unlock
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** Daily activity bar chart (last 14 days) */
function DailyActivityChart({ activities }: { activities: any[] }) {
  const today = new Date();
  const last14 = Array.from({ length: 14 }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() - (13 - i));
    return d.toISOString().slice(0, 10);
  });

  const actMap = new Map<string, any>();
  activities.forEach((a: any) => actMap.set(a.date, a));

  const maxKp = Math.max(1, ...last14.map((d) => actMap.get(d)?.kpEarned ?? 0));

  return (
    <div className="flex items-end gap-1.5 h-32">
      {last14.map((day) => {
        const act = actMap.get(day);
        const kp = act?.kpEarned ?? 0;
        const height = Math.max(2, (kp / maxKp) * 100);
        const isToday = day === today.toISOString().slice(0, 10);
        const date = new Date(day);

        return (
          <div key={day} className="flex flex-1 flex-col items-center gap-1 group relative">
            {/* Tooltip */}
            <div className="absolute bottom-full mb-1 hidden group-hover:block z-10">
              <div className="rounded-lg bg-gray-900 px-2 py-1 text-[10px] text-white whitespace-nowrap shadow-lg">
                <div className="font-semibold">{kp} KP earned</div>
                {act && (
                  <div className="text-gray-300">
                    {act.pagesRead ?? 0} pages · {act.readingMinutes ?? 0}m read
                  </div>
                )}
              </div>
            </div>
            {/* Bar */}
            <div
              className={cn(
                'w-full rounded-t-md transition-all duration-300',
                isToday ? 'bg-primary-600' : kp > 0 ? 'bg-primary-400' : 'bg-gray-200 dark:bg-gray-700',
              )}
              style={{ height: `${height}%` }}
            />
            {/* Date label */}
            <span className={cn(
              'text-[8px]',
              isToday ? 'text-primary-600 font-bold' : 'text-nova-text-muted',
            )}>
              {date.toLocaleDateString('en-US', { day: 'numeric' })}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ─── main component ─────────────────────────── */

export default function KnowledgePointsPage() {
  useDocumentTitle('Knowledge Points');

  const { data: engData, loading: engLoading } = useQuery(MY_ENGAGEMENT);
  const { data: actData, loading: actLoading } = useQuery(MY_DAILY_ACTIVITY, {
    variables: { days: 30 },
  });
  const { data: rankData } = useQuery(MY_RANK);
  const { data: myAchData } = useQuery(MY_ACHIEVEMENTS);
  const { data: allAchData } = useQuery(ALL_ACHIEVEMENTS);
  const { data: kpHistData } = useQuery(MY_KP_HISTORY, { variables: { limit: 20 } });

  const engagement = engData?.myEngagement;
  const activities = actData?.myDailyActivity ?? [];
  const rank = rankData?.myRank;
  const myAchievements = myAchData?.myAchievements ?? [];
  const allAchievements = allAchData?.allAchievements ?? [];
  const kpHistory = kpHistData?.myKpHistory ?? [];

  const todayKp = useMemo(() => {
    const todayStr = new Date().toISOString().slice(0, 10);
    const todayAct = activities.find((a: any) => a.date === todayStr);
    return todayAct?.kpEarned ?? 0;
  }, [activities]);

  const weekKp = useMemo(() => {
    const now = Date.now();
    const weekAgo = now - 7 * 24 * 60 * 60 * 1000;
    return activities
      .filter((a: any) => new Date(a.date).getTime() >= weekAgo)
      .reduce((sum: number, a: any) => sum + (a.kpEarned ?? 0), 0);
  }, [activities]);

  const dimensions = useMemo(() => {
    if (!engagement) return [];
    const maxDim = Math.max(
      engagement.explorerKp ?? 0,
      engagement.scholarKp ?? 0,
      engagement.connectorKp ?? 0,
      engagement.achieverKp ?? 0,
      engagement.dedicatedKp ?? 0,
      100,
    );
    return KP_DIMENSIONS.map((d) => ({
      ...d,
      value: engagement[d.key] ?? 0,
      max: maxDim,
    }));
  }, [engagement]);

  if (engLoading) return <LoadingOverlay />;
  if (!engagement) return <LoadingOverlay />;

  const currentTier = LEVEL_TIERS.find((t) => t.level === engagement.level) ?? LEVEL_TIERS[0]!;
  const nextTier = LEVEL_TIERS.find((t) => t.level === engagement.level + 1);
  const kpToNext = nextTier ? nextTier.kpRequired - engagement.totalKp : 0;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ─── Header ─── */}
      <div>
        <h1 className="text-2xl font-bold text-nova-text flex items-center gap-2">
          <TrophyIcon className="h-7 w-7 text-amber-500" />
          Knowledge Points Center
        </h1>
        <p className="mt-1 text-sm text-nova-text-secondary">
          Track your learning journey, earn KP, and climb the ranks
        </p>
      </div>

      {/* ─── Hero Stats ─── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total KP */}
        <Card className="bg-gradient-to-br from-amber-50 to-amber-100/50 dark:from-amber-900/20 dark:to-amber-900/10 border-amber-200 dark:border-amber-800">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500 text-white text-xl shadow-lg">
              {currentTier!.icon}
            </div>
            <div>
              <p className="text-2xl font-black text-amber-700 dark:text-amber-400">
                {formatNumber(engagement.totalKp)}
              </p>
              <p className="text-xs text-amber-600/80 dark:text-amber-400/60">Total KP</p>
            </div>
          </div>
        </Card>

        {/* Streak */}
        <Card className={cn(
          engagement.currentStreak >= 7
            ? 'bg-gradient-to-br from-orange-50 to-red-50 border-orange-200 dark:from-orange-900/20 dark:to-red-900/10 dark:border-orange-800'
            : '',
        )}>
          <div className="flex items-center gap-3">
            <div className={cn(
              'flex h-12 w-12 items-center justify-center rounded-xl',
              engagement.currentStreak >= 7
                ? 'bg-gradient-to-br from-orange-500 to-red-500 text-white'
                : 'bg-orange-100 text-orange-600 dark:bg-orange-900/30',
            )}>
              <FireIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-2xl font-black text-nova-text">
                {engagement.currentStreak}
                <span className="text-sm font-normal text-nova-text-muted ml-1">days</span>
              </p>
              <p className="text-xs text-nova-text-muted">
                Current Streak
                {engagement.streakMultiplier > 1 && (
                  <Badge variant="warning" size="xs" className="ml-1">
                    {engagement.streakMultiplier}x bonus
                  </Badge>
                )}
              </p>
            </div>
          </div>
        </Card>

        {/* Rank */}
        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-100 text-primary-600 dark:bg-primary-900/30">
              <ChartBarIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-2xl font-black text-nova-text">
                #{rank?.rank ?? '—'}
              </p>
              <p className="text-xs text-nova-text-muted">
                Global Rank
                {rank?.percentile && (
                  <span className="ml-1 text-primary-600 font-semibold">
                    Top {100 - Math.round(rank.percentile)}%
                  </span>
                )}
              </p>
            </div>
          </div>
        </Card>

        {/* Today */}
        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-100 text-green-600 dark:bg-green-900/30">
              <ArrowTrendingUpIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-2xl font-black text-nova-text">
                +{todayKp}
              </p>
              <p className="text-xs text-nova-text-muted">
                KP Today · {weekKp} this week
              </p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* ─── Level Progression ─── */}
        <Card>
          <CardHeader
            title="Level Progression"
            description={
              nextTier
                ? `${formatNumber(kpToNext)} KP to Level ${nextTier.level}: ${nextTier.name}`
                : 'Maximum level reached!'
            }
          />
          <div className="mt-4">
            <LevelTierTrack currentLevel={engagement.level} totalKp={engagement.totalKp} />
          </div>
        </Card>

        {/* ─── KP Dimensions Radar ─── */}
        <Card>
          <CardHeader
            title="KP Dimensions"
            description="Your knowledge profile across 5 dimensions"
          />
          <div className="mt-4 flex flex-col items-center">
            <div className="h-60 w-60">
              <KPRadarChart
                dimensions={dimensions.map((d) => ({
                  name: d.name,
                  value: d.value,
                  max: d.max,
                }))}
              />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 w-full sm:grid-cols-3">
              {dimensions.map((dim) => (
                <div key={dim.key} className="flex items-center gap-2">
                  <div className={cn('flex h-8 w-8 items-center justify-center rounded-lg', dim.bg)}>
                    <dim.icon className={cn('h-4 w-4', dim.color)} />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-nova-text">{dim.name}</p>
                    <p className="text-[10px] text-nova-text-muted">{formatNumber(dim.value)} KP</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* ─── Activity Heatmap ─── */}
        <Card>
          <CardHeader
            title="Activity Heatmap"
            description="Last 30 days of KP earning"
          />
          <div className="mt-4">
            {actLoading ? (
              <LoadingOverlay />
            ) : (
              <ActivityHeatmap activities={activities} />
            )}
          </div>
        </Card>

        {/* ─── Daily Activity Chart ─── */}
        <Card>
          <CardHeader
            title="Daily KP Earned"
            description="Last 14 days"
          />
          <div className="mt-4">
            {actLoading ? (
              <LoadingOverlay />
            ) : (
              <DailyActivityChart activities={activities} />
            )}
          </div>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* ─── Streak Info ─── */}
        <Card>
          <CardHeader title="Streak Details" />
          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-orange-400 to-red-500 text-white">
                  <FireIcon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-nova-text">Current Streak</p>
                  <p className="text-xs text-nova-text-muted">Keep it going!</p>
                </div>
              </div>
              <span className="text-2xl font-black text-nova-text">{engagement.currentStreak} days</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-100 text-amber-600 dark:bg-amber-900/30">
                  <TrophyIcon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-nova-text">Longest Streak</p>
                  <p className="text-xs text-nova-text-muted">Personal best</p>
                </div>
              </div>
              <span className="text-2xl font-black text-nova-text">{engagement.longestStreak} days</span>
            </div>
            {engagement.streakMultiplier > 1 && (
              <div className="rounded-xl bg-gradient-to-r from-orange-50 to-amber-50 p-4 dark:from-orange-900/10 dark:to-amber-900/10">
                <div className="flex items-center gap-2">
                  <SparklesIcon className="h-5 w-5 text-amber-500" />
                  <span className="text-sm font-semibold text-amber-700 dark:text-amber-400">
                    Streak Bonus Active: {engagement.streakMultiplier}x KP multiplier!
                  </span>
                </div>
                <p className="mt-1 text-xs text-amber-600/70 dark:text-amber-400/60">
                  Maintain your reading streak to earn bonus KP on every activity
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* ─── Achievement Summary ─── */}
        <Card>
          <CardHeader
            title="Achievements"
            action={
              <Link to="/achievements">
                <Button variant="ghost" size="xs" rightIcon={<ChevronRightIcon className="h-3.5 w-3.5" />}>
                  View All
                </Button>
              </Link>
            }
          />
          <div className="mt-4">
            <div className="mb-4 flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-100 text-amber-600 dark:bg-amber-900/30">
                <TrophyIcon className="h-7 w-7" />
              </div>
              <div className="flex-1">
                <p className="text-lg font-bold text-nova-text">
                  {myAchievements.length} <span className="text-sm font-normal text-nova-text-muted">of {allAchievements.length}</span>
                </p>
                <ProgressBar
                  value={myAchievements.length}
                  max={Math.max(allAchievements.length, 1)}
                  size="sm"
                  color="accent"
                  className="mt-1"
                />
              </div>
            </div>

            {/* Recent achievements */}
            <div className="space-y-2">
              {myAchievements.slice(0, 4).map((ua: any) => {
                const ach = ua.achievement;
                return (
                  <div key={ua.id} className="flex items-center gap-3 rounded-lg p-2 hover:bg-nova-surface-hover transition-colors">
                    <span className="text-lg">{ach?.icon || '🏆'}</span>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-nova-text">{ach?.name}</p>
                      <p className="text-[10px] text-nova-text-muted">{formatDate(ua.earnedAt)}</p>
                    </div>
                    <Badge variant="kp-gold" size="xs">+{ach?.kpReward} KP</Badge>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      </div>

      {/* ─── KP History ─── */}
      {kpHistory.length > 0 && (
        <Card>
          <CardHeader title="KP History" icon={<ClockIcon className="h-5 w-5" />} />
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-nova-border bg-nova-surface text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Dimension</th>
                  <th className="px-4 py-3 text-right">Points</th>
                  <th className="px-4 py-3 text-right">Balance</th>
                  <th className="px-4 py-3">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nova-border">
                {kpHistory.map((entry: any) => {
                  const isPositive = ['AWARD', 'BONUS', 'ADMIN_ADJUST'].includes(entry.action);
                  return (
                    <tr key={entry.id} className="hover:bg-nova-surface-hover transition-colors">
                      <td className="px-4 py-3 text-xs text-nova-text-muted whitespace-nowrap">{formatDate(entry.createdAt)}</td>
                      <td className="px-4 py-3">
                        <Badge variant={isPositive ? 'success' : 'danger'} size="xs">{entry.action}</Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-nova-text-muted">{entry.dimension || '—'}</td>
                      <td className={cn('px-4 py-3 text-right font-bold text-sm', isPositive ? 'text-green-600' : 'text-red-600')}>
                        {isPositive ? '+' : '-'}{entry.points}
                      </td>
                      <td className="px-4 py-3 text-right text-xs font-medium text-nova-text">{entry.balanceAfter?.toLocaleString() ?? '—'}</td>
                      <td className="px-4 py-3 text-xs text-nova-text-muted max-w-xs truncate">{entry.description || '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ─── Tips Section ─── */}
      <Card className="bg-gradient-to-r from-primary-50 to-accent-50 dark:from-primary-900/10 dark:to-accent-900/10">
        <div className="text-center">
          <h3 className="text-sm font-semibold text-nova-text mb-2">💡 How to Earn More KP</h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { icon: BookOpenIcon, text: 'Read or listen daily to maintain streaks', kp: '+5-20 KP' },
              { icon: StarIcon, text: 'Write book reviews and rate books', kp: '+10-15 KP' },
              { icon: TrophyIcon, text: 'Complete achievements for bonus rewards', kp: '+10-200 KP' },
              { icon: FireIcon, text: 'Maintain streaks for KP multiplier bonuses', kp: 'Up to 3x' },
            ].map((tip, i) => (
              <div key={i} className="flex items-center gap-2 rounded-lg bg-white/50 p-3 dark:bg-gray-800/30">
                <tip.icon className="h-5 w-5 flex-shrink-0 text-primary-500" />
                <div className="text-left">
                  <p className="text-xs text-nova-text">{tip.text}</p>
                  <p className="text-[10px] font-semibold text-primary-600">{tip.kp}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
}

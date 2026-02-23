/**
 * ReadingInsightsPage — analytics dashboard showing the user's reading behaviour,
 * speed, session patterns, engagement heatmap, and completion predictions.
 */

import { useQuery } from '@apollo/client';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Tooltip as ChartTooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import {
  ClockIcon,
  BookOpenIcon,
  SparklesIcon,
  ChartBarIcon,
  FireIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import {
  MY_READING_SPEED,
  MY_SESSION_PATTERNS,
  MY_ENGAGEMENT_HEATMAP,
  MY_COMPLETION_PREDICTIONS,
} from '@/graphql/queries/intelligence';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  ChartTooltip,
  Legend,
  Filler,
);

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HOURS = Array.from({ length: 24 }, (_, i) => `${i}:00`);

function speedCategory(wpm: number): string {
  if (wpm < 150) return 'Slow';
  if (wpm < 250) return 'Average';
  if (wpm < 400) return 'Fast';
  return 'Speed reader';
}

function speedColor(wpm: number): string {
  if (wpm < 150) return 'text-amber-500';
  if (wpm < 250) return 'text-blue-500';
  if (wpm < 400) return 'text-green-500';
  return 'text-primary-500';
}

export default function ReadingInsightsPage() {
  useDocumentTitle('Reading Insights');

  const { data: speedData, loading: speedLoading } = useQuery(MY_READING_SPEED);
  const { data: patternData, loading: patternLoading } = useQuery(MY_SESSION_PATTERNS);
  const { data: heatmapData, loading: heatmapLoading } = useQuery(MY_ENGAGEMENT_HEATMAP, {
    variables: { days: 90 },
  });
  const { data: predData, loading: predLoading } = useQuery(MY_COMPLETION_PREDICTIONS);

  const loading = speedLoading || patternLoading || heatmapLoading || predLoading;

  if (loading) return <LoadingOverlay />;

  const speed = speedData?.myReadingSpeed;
  const patterns = patternData?.mySessionPatterns;
  const heatmap = heatmapData?.myEngagementHeatmap;
  const predictions = predData?.myCompletionPredictions ?? [];

  const hasData = speed || patterns;

  if (!hasData) {
    return (
      <div className="py-16 animate-fade-in">
        <EmptyState
          icon={<ChartBarIcon />}
          title="No reading data yet"
          description="Start reading digital content to see your personalised reading analytics here."
        />
      </div>
    );
  }

  // --- Session Patterns Bar Chart ---
  const sessionsPerDayChart = patterns
    ? {
        labels: DAYS,
        datasets: [
          {
            label: 'Sessions',
            data: DAYS.map((_, idx) => {
              // Use day-level breakdown from API if available, otherwise spread weekly total
              if (Array.isArray(patterns.sessionsPerDay) && patterns.sessionsPerDay.length > idx) {
                return patterns.sessionsPerDay[idx] ?? 0;
              }
              return patterns.sessionsPerWeek
                ? Math.round(patterns.sessionsPerWeek / 7)
                : 0;
            }),
            backgroundColor: 'rgba(99,102,241,0.6)',
            borderRadius: 6,
          },
        ],
      }
    : null;

  // --- Heatmap data for hourly activity ---
  const hourlyChart = heatmap?.hours
    ? {
        labels: HOURS,
        datasets: [
          {
            label: 'Activity',
            data: heatmap.hours,
            fill: true,
            borderColor: 'rgba(99,102,241,0.8)',
            backgroundColor: 'rgba(99,102,241,0.15)',
            tension: 0.4,
            pointRadius: 2,
          },
        ],
      }
    : null;

  // --- Completion Predictions Doughnut ---
  const completionLabels = predictions.slice(0, 5).map((p: any) =>
    p.title.length > 20 ? p.title.slice(0, 20) + '…' : p.title,
  );
  const completionValues = predictions.slice(0, 5).map((p: any) => Math.round(p.completionProbability * 100));
  const completionChart =
    predictions.length > 0
      ? {
          labels: completionLabels,
          datasets: [
            {
              data: completionValues,
              backgroundColor: [
                'rgba(99,102,241,0.7)',
                'rgba(16,185,129,0.7)',
                'rgba(245,158,11,0.7)',
                'rgba(239,68,68,0.7)',
                'rgba(139,92,246,0.7)',
              ],
              borderWidth: 0,
            },
          ],
        }
      : null;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-nova-text">Reading Insights</h1>
        <p className="text-sm text-nova-text-secondary">
          Personalised analytics powered by your reading behaviour
        </p>
      </div>

      {/* KPIs row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {speed && (
          <Card className="flex items-center gap-4">
            <div className="rounded-lg bg-primary-50 p-3 dark:bg-primary-900/20">
              <BookOpenIcon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                Reading Speed
              </p>
              <p className={`text-xl font-bold ${speedColor(speed.wordsPerMinute)}`}>
                {speed.wordsPerMinute} <span className="text-xs font-normal">wpm</span>
              </p>
              <p className="text-[11px] text-nova-text-muted">
                {speed.category ?? speedCategory(speed.wordsPerMinute)} — {speed.sessionsAnalyzed} sessions
              </p>
            </div>
          </Card>
        )}

        {patterns && (
          <>
            <Card className="flex items-center gap-4">
              <div className="rounded-lg bg-green-50 p-3 dark:bg-green-900/20">
                <ClockIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                  Avg Session
                </p>
                <p className="text-xl font-bold text-nova-text">
                  {patterns.avgSessionMinutes} <span className="text-xs font-normal">min</span>
                </p>
                <p className="text-[11px] text-nova-text-muted">
                  {patterns.totalSessions} total sessions
                </p>
              </div>
            </Card>

            <Card className="flex items-center gap-4">
              <div className="rounded-lg bg-amber-50 p-3 dark:bg-amber-900/20">
                <FireIcon className="h-6 w-6 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                  Sessions / Week
                </p>
                <p className="text-xl font-bold text-nova-text">{patterns.sessionsPerWeek}</p>
                <p className="text-[11px] text-nova-text-muted">
                  Peak: {patterns.peakDay} at {patterns.peakHour}:00
                </p>
              </div>
            </Card>

            <Card className="flex items-center gap-4">
              <div className="rounded-lg bg-purple-50 p-3 dark:bg-purple-900/20">
                <SparklesIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                  Preferred Time
                </p>
                <p className="text-xl font-bold text-nova-text capitalize">
                  {patterns.preferredTime ?? 'N/A'}
                </p>
                <p className="text-[11px] text-nova-text-muted">Based on session history</p>
              </div>
            </Card>
          </>
        )}
      </div>

      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Hourly activity line chart */}
        {hourlyChart && (
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-nova-text">Hourly Reading Activity</h3>
              <Badge variant="info" size="sm">Last 90 days</Badge>
            </CardHeader>
            <div className="p-4 pt-0">
              <Line
                data={hourlyChart}
                options={{
                  responsive: true,
                  plugins: { legend: { display: false } },
                  scales: {
                    y: {
                      beginAtZero: true,
                      grid: { color: 'rgba(0,0,0,0.04)' },
                      ticks: { precision: 0 },
                    },
                    x: {
                      grid: { display: false },
                      ticks: {
                        maxTicksLimit: 12,
                        font: { size: 10 },
                      },
                    },
                  },
                }}
              />
            </div>
          </Card>
        )}

        {/* Session patterns bar */}
        {sessionsPerDayChart && (
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-nova-text">Weekly Sessions</h3>
              <Badge variant="info" size="sm">{patterns.sessionsPerWeek}/week</Badge>
            </CardHeader>
            <div className="p-4 pt-0">
              <Bar
                data={sessionsPerDayChart}
                options={{
                  responsive: true,
                  plugins: { legend: { display: false } },
                  scales: {
                    y: {
                      beginAtZero: true,
                      grid: { color: 'rgba(0,0,0,0.04)' },
                      ticks: { precision: 0 },
                    },
                    x: { grid: { display: false } },
                  },
                }}
              />
            </div>
          </Card>
        )}
      </div>

      {/* Completion predictions */}
      {predictions.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <CardHeader>
              <h3 className="font-semibold text-nova-text">Finish Probability</h3>
            </CardHeader>
            <div className="flex items-center justify-center p-4 pt-0">
              {completionChart && (
                <Doughnut
                  data={completionChart}
                  options={{
                    responsive: true,
                    cutout: '60%',
                    plugins: {
                      legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, padding: 8, font: { size: 10 } },
                      },
                    },
                  }}
                />
              )}
            </div>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <h3 className="font-semibold text-nova-text">Completion Predictions</h3>
            </CardHeader>
            <div className="space-y-3 p-4 pt-0">
              {predictions.map((pred: any) => {
                const pct = Math.round(pred.completionProbability * 100);
                const progress = Math.round((pred.currentProgress ?? 0) * 100);
                return (
                  <div key={pred.assetId} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <p className="truncate text-sm font-medium text-nova-text">{pred.title}</p>
                      <div className="ml-2 flex items-center gap-2">
                        <Badge
                          variant={pct >= 70 ? 'success' : pct >= 40 ? 'warning' : 'danger'}
                          size="sm"
                        >
                          {pct}% likely
                        </Badge>
                        {pred.estimatedDays != null && (
                          <span className="text-xs text-nova-text-muted">
                            ~{pred.estimatedDays}d
                          </span>
                        )}
                      </div>
                    </div>
                    <ProgressBar value={progress} max={100} size="sm" color="primary" />
                    <p className="text-[11px] text-nova-text-muted">{progress}% read</p>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      )}

      {/* Engagement heatmap grid */}
      {heatmap?.heatmap && Array.isArray(heatmap.heatmap) && (
        <Card>
          <CardHeader>
            <h3 className="font-semibold text-nova-text">90-Day Engagement Heatmap</h3>
          </CardHeader>
          <div className="overflow-x-auto p-4 pt-2">
            <div className="min-w-[600px]">
              <div className="mb-1 flex">
                <div className="w-10" />
                {HOURS.filter((_, i) => i % 3 === 0).map((h) => (
                  <span key={h} className="flex-1 text-center text-[10px] text-nova-text-muted">
                    {h}
                  </span>
                ))}
              </div>
              {DAYS.map((day, di) => (
                <div key={day} className="flex items-center gap-0.5 mb-0.5">
                  <span className="w-10 text-right text-[10px] font-medium text-nova-text-muted pr-2">
                    {day}
                  </span>
                  {Array.from({ length: 24 }, (_, hi) => {
                    const value = heatmap.heatmap?.[di]?.[hi] ?? 0;
                    const max = Math.max(
                      1,
                      ...heatmap.heatmap.flat().filter((v: any) => typeof v === 'number'),
                    );
                    const intensity = value / max;
                    return (
                      <div
                        key={hi}
                        className="flex-1 rounded-sm"
                        style={{
                          height: 18,
                          backgroundColor:
                            intensity === 0
                              ? 'rgba(0,0,0,0.04)'
                              : `rgba(99,102,241,${0.15 + intensity * 0.75})`,
                        }}
                        title={`${day} ${hi}:00 — ${value} sessions`}
                      />
                    );
                  })}
                </div>
              ))}
              <div className="mt-2 flex items-center justify-end gap-1 text-[10px] text-nova-text-muted">
                <span>Less</span>
                {[0, 0.25, 0.5, 0.75, 1].map((v) => (
                  <div
                    key={v}
                    className="h-3 w-3 rounded-sm"
                    style={{
                      backgroundColor:
                        v === 0
                          ? 'rgba(0,0,0,0.04)'
                          : `rgba(99,102,241,${0.15 + v * 0.75})`,
                    }}
                  />
                ))}
                <span>More</span>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

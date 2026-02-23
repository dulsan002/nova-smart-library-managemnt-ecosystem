/**
 * AdminDashboardPage — admin overview with key metrics, overdue warnings,
 * recent activity, and AI model health.
 */

import { useQuery } from '@apollo/client';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import {
  UsersIcon,
  BookOpenIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  ArrowTrendingUpIcon,
  CubeIcon,
  UserGroupIcon,
  BriefcaseIcon,
  WrenchScrewdriverIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { GET_USERS } from '@/graphql/queries/admin';
import { GET_BOOKS } from '@/graphql/queries/catalog';
import { ALL_BORROWS, OVERDUE_BORROWS } from '@/graphql/queries/circulation';
import { SECURITY_EVENTS } from '@/graphql/queries/governance';
import { AI_MODELS, OVERDUE_PREDICTIONS, CHURN_PREDICTIONS } from '@/graphql/queries/intelligence';
import { GET_ASSET_STATS } from '@/graphql/queries/assets';
import { GET_HR_STATS } from '@/graphql/queries/hr';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { timeAgo } from '@/lib/utils';
import { Link } from 'react-router-dom';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, ChartTooltip, Legend);

export default function AdminDashboardPage() {
  useDocumentTitle('Admin Dashboard');

  const { data: usersData, loading: uL } = useQuery(GET_USERS, { variables: { first: 1 } });
  const { data: booksData, loading: bL } = useQuery(GET_BOOKS, { variables: { first: 1 } });
  const { loading: brL } = useQuery(ALL_BORROWS, { variables: { first: 1 } });
  const { data: overdueData, loading: oL } = useQuery(OVERDUE_BORROWS, { variables: { limit: 5 } });
  const { data: secData } = useQuery(SECURITY_EVENTS, { variables: { resolved: false, limit: 5 } });
  const { data: modelsData } = useQuery(AI_MODELS);
  const { data: overduePred } = useQuery(OVERDUE_PREDICTIONS, { variables: { limit: 5 } });
  const { data: churnPred } = useQuery(CHURN_PREDICTIONS, { variables: { limit: 5 } });
  const { data: assetStatsData } = useQuery(GET_ASSET_STATS);
  const { data: hrStatsData } = useQuery(GET_HR_STATS);

  const loading = uL || bL || brL || oL;

  const totalUsers = usersData?.users?.totalCount ?? 0;
  const totalBooks = booksData?.books?.totalCount ?? 0;
  const overdueList = overdueData?.overdueBorrows ?? [];
  const securityEvents = secData?.securityEvents ?? [];
  const models = modelsData?.aiModels ?? [];
  const activeModels = models.filter((m: any) => m.isActive);
  const overduePredictions = overduePred?.overduePredictions ?? [];
  const churnList = churnPred?.churnPredictions ?? [];
  const assetStats = assetStatsData?.assetStats;
  const hrStats = hrStatsData?.hrStats;

  const riskLevelColor = (level: string) => {
    if (level === 'HIGH') return 'danger';
    if (level === 'MEDIUM') return 'warning';
    return 'success';
  };

  // Chart: Model types
  const modelTypeMap = models.reduce((acc: Record<string, number>, m: any) => {
    acc[m.modelType] = (acc[m.modelType] ?? 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  const modelChart = {
    labels: Object.keys(modelTypeMap),
    datasets: [
      {
        data: Object.values(modelTypeMap),
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
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold text-nova-text">Admin Dashboard</h1>

      {loading ? (
        <LoadingOverlay />
      ) : (
        <>
          {/* KPI cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              icon={<UsersIcon className="h-6 w-6" />}
              label="Total Users"
              value={totalUsers}
              color="primary"
            />
            <StatCard
              icon={<BookOpenIcon className="h-6 w-6" />}
              label="Total Books"
              value={totalBooks}
              color="green"
            />
            <StatCard
              icon={<ExclamationTriangleIcon className="h-6 w-6" />}
              label="Overdue Borrows"
              value={overdueList.length}
              color="amber"
            />
            <StatCard
              icon={<CpuChipIcon className="h-6 w-6" />}
              label="Active AI Models"
              value={`${activeModels.length}/${models.length}`}
              color="purple"
            />
          </div>

          {/* Enterprise Quick Access */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link to="/admin/assets" className="group">
              <Card className="p-4 transition-all group-hover:ring-2 group-hover:ring-primary-300 dark:group-hover:ring-primary-700">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg p-2 bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600">
                    <CubeIcon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-nova-text">Asset Management</p>
                    <p className="text-xs text-nova-text-muted">
                      {assetStats ? `${assetStats.totalAssets} assets · ${assetStats.maintenanceOverdue} overdue` : 'Loading...'}
                    </p>
                  </div>
                </div>
              </Card>
            </Link>
            <Link to="/admin/employees" className="group">
              <Card className="p-4 transition-all group-hover:ring-2 group-hover:ring-primary-300 dark:group-hover:ring-primary-700">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg p-2 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600">
                    <UserGroupIcon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-nova-text">HR & Employees</p>
                    <p className="text-xs text-nova-text-muted">
                      {hrStats ? `${hrStats.activeEmployees} active · ${hrStats.onLeaveCount} on leave` : 'Loading...'}
                    </p>
                  </div>
                </div>
              </Card>
            </Link>
            <Link to="/admin/employees" className="group">
              <Card className="p-4 transition-all group-hover:ring-2 group-hover:ring-primary-300 dark:group-hover:ring-primary-700">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg p-2 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600">
                    <BriefcaseIcon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-nova-text">Recruitment</p>
                    <p className="text-xs text-nova-text-muted">
                      {hrStats ? `${hrStats.openVacancies} open · ${hrStats.pendingApplications} pending` : 'Loading...'}
                    </p>
                  </div>
                </div>
              </Card>
            </Link>
            <Link to="/admin/settings" className="group">
              <Card className="p-4 transition-all group-hover:ring-2 group-hover:ring-primary-300 dark:group-hover:ring-primary-700">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg p-2 bg-slate-50 dark:bg-slate-900/20 text-slate-600">
                    <WrenchScrewdriverIcon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-nova-text">System Settings</p>
                    <p className="text-xs text-nova-text-muted">Configuration & policies</p>
                  </div>
                </div>
              </Card>
            </Link>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Overdue predictions */}
            <Card>
              <CardHeader>
                <h3 className="font-semibold text-nova-text flex items-center gap-2">
                  <ArrowTrendingUpIcon className="h-5 w-5 text-amber-500" />
                  Overdue Risk Predictions
                </h3>
              </CardHeader>
              <div className="divide-y divide-nova-border">
                {overduePredictions.length === 0 ? (
                  <p className="p-4 text-sm text-nova-text-muted">No predictions available</p>
                ) : (
                  overduePredictions.map((p: any) => (
                    <div key={p.borrowId} className="flex items-center justify-between px-4 py-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-nova-text">{p.bookTitle}</p>
                        <p className="text-xs text-nova-text-muted">{p.userEmail}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-nova-text">
                          {Math.round(p.probability * 100)}%
                        </span>
                        <Badge variant={riskLevelColor(p.riskLevel)} size="sm">
                          {p.riskLevel}
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>

            {/* Churn risk */}
            <Card>
              <CardHeader>
                <h3 className="font-semibold text-nova-text flex items-center gap-2">
                  <UsersIcon className="h-5 w-5 text-red-500" />
                  User Churn Risk
                </h3>
              </CardHeader>
              <div className="divide-y divide-nova-border">
                {churnList.length === 0 ? (
                  <p className="p-4 text-sm text-nova-text-muted">No churn predictions</p>
                ) : (
                  churnList.map((c: any) => (
                    <div key={c.userId} className="flex items-center justify-between px-4 py-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-nova-text">{c.userEmail}</p>
                        <p className="text-xs text-nova-text-muted">
                          {c.weeksInactive} weeks inactive
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-nova-text">
                          {Math.round(c.churnProbability * 100)}%
                        </span>
                        <Badge variant={riskLevelColor(c.riskLevel)} size="sm">
                          {c.riskLevel}
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Security events */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <h3 className="font-semibold text-nova-text flex items-center gap-2">
                  <ShieldCheckIcon className="h-5 w-5 text-red-500" />
                  Unresolved Security Events
                </h3>
              </CardHeader>
              <div className="divide-y divide-nova-border">
                {securityEvents.length === 0 ? (
                  <p className="p-4 text-sm text-nova-text-muted">No unresolved events</p>
                ) : (
                  securityEvents.map((ev: any) => (
                    <div key={ev.id} className="flex items-center justify-between px-4 py-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-nova-text">
                          {ev.eventType.replace(/_/g, ' ')}
                        </p>
                        <p className="text-xs text-nova-text-muted">{ev.description}</p>
                      </div>
                      <div className="flex items-center gap-2 text-right">
                        <Badge
                          variant={
                            ev.severity === 'CRITICAL'
                              ? 'danger'
                              : ev.severity === 'HIGH'
                                ? 'warning'
                                : 'info'
                          }
                          size="sm"
                        >
                          {ev.severity}
                        </Badge>
                        <span className="text-[11px] text-nova-text-muted">
                          {timeAgo(ev.createdAt)}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>

            {/* AI model distribution */}
            <Card>
              <CardHeader>
                <h3 className="font-semibold text-nova-text">AI Models by Type</h3>
              </CardHeader>
              <div className="flex items-center justify-center p-4 pt-0">
                {models.length > 0 ? (
                  <Doughnut
                    data={modelChart}
                    options={{
                      responsive: true,
                      cutout: '55%',
                      plugins: {
                        legend: {
                          position: 'bottom',
                          labels: { boxWidth: 12, padding: 8, font: { size: 10 } },
                        },
                      },
                    }}
                  />
                ) : (
                  <p className="py-8 text-sm text-nova-text-muted">No models</p>
                )}
              </div>
            </Card>
          </div>

          {/* Current overdue */}
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-nova-text flex items-center gap-2">
                <ClockIcon className="h-5 w-5 text-amber-500" />
                Current Overdue Items
              </h3>
            </CardHeader>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                    <th className="px-4 py-2">Book</th>
                    <th className="px-4 py-2">Borrower</th>
                    <th className="px-4 py-2">Barcode</th>
                    <th className="px-4 py-2">Due Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-nova-border">
                  {overdueList.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-4 py-6 text-center text-nova-text-muted">
                        No overdue items
                      </td>
                    </tr>
                  ) : (
                    overdueList.map((b: any) => (
                      <tr key={b.id} className="hover:bg-nova-surface-hover transition-colors">
                        <td className="px-4 py-2 font-medium text-nova-text">
                          {b.bookCopy?.book?.title ?? '—'}
                        </td>
                        <td className="px-4 py-2 text-nova-text-secondary">
                          {b.user?.email ?? '—'}
                        </td>
                        <td className="px-4 py-2 font-mono text-xs text-nova-text-muted">
                          {b.bookCopy?.barcode}
                        </td>
                        <td className="px-4 py-2 text-red-500 font-medium">
                          {b.dueDate ? new Date(b.dueDate).toLocaleDateString() : '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

/* ─── small stat card ──────────────────────────────── */
function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
}) {
  const bgMap: Record<string, string> = {
    primary: 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400',
    green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    amber: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
    red: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400',
  };

  return (
    <Card className="flex items-center gap-4">
      <div className={`rounded-lg p-3 ${bgMap[color] ?? bgMap.primary}`}>{icon}</div>
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-nova-text-muted">{label}</p>
        <p className="text-2xl font-bold text-nova-text">{value}</p>
      </div>
    </Card>
  );
}

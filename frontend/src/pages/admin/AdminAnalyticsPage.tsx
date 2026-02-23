/**
 * AdminAnalyticsPage — predictive analytics: overdue risk, demand forecasts,
 * churn predictions, collection gap analysis.
 */

import { useQuery } from '@apollo/client';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import {
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  UsersIcon,
  RectangleGroupIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import {
  OVERDUE_PREDICTIONS,
  DEMAND_FORECASTS,
  CHURN_PREDICTIONS,
  COLLECTION_GAPS,
} from '@/graphql/queries/intelligence';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Tabs } from '@/components/ui/Tabs';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { useState } from 'react';

ChartJS.register(CategoryScale, LinearScale, BarElement, ChartTooltip, Legend);

const riskBadge = (level: string) => {
  const map: Record<string, 'danger' | 'warning' | 'success'> = {
    HIGH: 'danger',
    MEDIUM: 'warning',
    LOW: 'success',
  };
  return map[level] ?? 'neutral' as any;
};

const severityBadge = (sev: string) => {
  const map: Record<string, 'danger' | 'warning' | 'info'> = {
    CRITICAL: 'danger',
    HIGH: 'danger',
    MEDIUM: 'warning',
    LOW: 'info',
  };
  return map[sev] ?? 'neutral' as any;
};

export default function AdminAnalyticsPage() {
  useDocumentTitle('Predictive Analytics');

  const [activeTab, setActiveTab] = useState(0);

  const { data: overdueData, loading: oL } = useQuery(OVERDUE_PREDICTIONS, {
    variables: { limit: 20 },
  });
  const { data: demandData, loading: dL } = useQuery(DEMAND_FORECASTS, {
    variables: { limit: 20 },
  });
  const { data: churnData, loading: cL } = useQuery(CHURN_PREDICTIONS, {
    variables: { limit: 20 },
  });
  const { data: gapData, loading: gL } = useQuery(COLLECTION_GAPS);

  const loading = oL || dL || cL || gL;

  const overduePreds = overdueData?.overduePredictions ?? [];
  const forecasts = demandData?.demandForecasts ?? [];
  const churnPreds = churnData?.churnPredictions ?? [];
  const gaps = gapData?.collectionGaps ?? [];

  // Demand forecast chart
  const demandChart = {
    labels: forecasts.slice(0, 10).map((f: any) =>
      f.bookTitle.length > 25 ? f.bookTitle.slice(0, 25) + '…' : f.bookTitle,
    ),
    datasets: [
      {
        label: 'Predicted Borrows',
        data: forecasts.slice(0, 10).map((f: any) => f.predictedBorrows),
        backgroundColor: 'rgba(99,102,241,0.6)',
        borderRadius: 4,
      },
      {
        label: 'Recommended Copies',
        data: forecasts.slice(0, 10).map((f: any) => f.recommendedCopies),
        backgroundColor: 'rgba(16,185,129,0.6)',
        borderRadius: 4,
      },
    ],
  };

  const tabs = [
    { label: 'Overdue Risk', content: null },
    { label: 'Demand Forecasts', content: null },
    { label: 'Churn Risk', content: null },
    { label: 'Collection Gaps', content: null },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold text-nova-text">Predictive Analytics</h1>
      <p className="text-sm text-nova-text-secondary">
        AI-powered predictions to help you make data-driven decisions.
      </p>

      <Tabs tabs={tabs} active={activeTab} onChange={setActiveTab} />

      {loading ? (
        <LoadingOverlay />
      ) : (
        <>
          {/* Overdue risk */}
          {activeTab === 0 && (
            <>
              {overduePreds.length === 0 ? (
                <EmptyState
                  icon={<ExclamationTriangleIcon />}
                  title="No overdue predictions"
                  description="The AI model has not identified any overdue risks."
                />
              ) : (
                <Card padding="none">
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                          <th className="px-4 py-3">Book</th>
                          <th className="px-4 py-3">Borrower</th>
                          <th className="px-4 py-3">Probability</th>
                          <th className="px-4 py-3">Risk Level</th>
                          <th className="px-4 py-3">Contributing Factors</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-nova-border">
                        {overduePreds.map((p: any) => (
                          <tr key={p.borrowId} className="hover:bg-nova-surface-hover transition-colors">
                            <td className="px-4 py-3 font-medium text-nova-text">{p.bookTitle}</td>
                            <td className="px-4 py-3 text-nova-text-secondary">{p.userEmail}</td>
                            <td className="px-4 py-3">
                              <span className="text-sm font-semibold text-nova-text">
                                {Math.round(p.probability * 100)}%
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <Badge variant={riskBadge(p.riskLevel)} size="sm">
                                {p.riskLevel}
                              </Badge>
                            </td>
                            <td className="px-4 py-3">
                              {Array.isArray(p.contributingFactors)
                                ? p.contributingFactors.map((f: string, i: number) => (
                                    <Badge key={i} variant="neutral" size="sm" className="mr-1 mb-1">
                                      {f}
                                    </Badge>
                                  ))
                                : <span className="text-xs text-nova-text-muted">—</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </>
          )}

          {/* Demand forecasts */}
          {activeTab === 1 && (
            <>
              {forecasts.length === 0 ? (
                <EmptyState
                  icon={<ArrowTrendingUpIcon />}
                  title="No demand forecasts"
                  description="Insufficient data for demand forecasting."
                />
              ) : (
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <h3 className="font-semibold text-nova-text">Demand vs. Recommended Copies</h3>
                    </CardHeader>
                    <div className="p-4 pt-0">
                      <Bar
                        data={demandChart}
                        options={{
                          responsive: true,
                          indexAxis: 'y',
                          plugins: {
                            legend: {
                              position: 'top',
                              labels: { boxWidth: 12, font: { size: 11 } },
                            },
                          },
                          scales: {
                            x: {
                              beginAtZero: true,
                              grid: { color: 'rgba(0,0,0,0.04)' },
                              ticks: { precision: 0 },
                            },
                            y: {
                              grid: { display: false },
                              ticks: { font: { size: 10 } },
                            },
                          },
                        }}
                      />
                    </div>
                  </Card>

                  <Card padding="none">
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                            <th className="px-4 py-3">Book</th>
                            <th className="px-4 py-3">Trend</th>
                            <th className="px-4 py-3">Predicted Borrows</th>
                            <th className="px-4 py-3">Recommended Copies</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-nova-border">
                          {forecasts.map((f: any) => (
                            <tr key={f.bookId} className="hover:bg-nova-surface-hover transition-colors">
                              <td className="px-4 py-3 font-medium text-nova-text">{f.bookTitle}</td>
                              <td className="px-4 py-3">
                                <Badge
                                  variant={f.trend === 'UP' ? 'success' : f.trend === 'DOWN' ? 'danger' : 'neutral'}
                                  size="sm"
                                >
                                  {f.trend}
                                </Badge>
                              </td>
                              <td className="px-4 py-3 text-nova-text">{f.predictedBorrows}</td>
                              <td className="px-4 py-3 font-semibold text-primary-600">
                                {f.recommendedCopies}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                </div>
              )}
            </>
          )}

          {/* Churn risk */}
          {activeTab === 2 && (
            <>
              {churnPreds.length === 0 ? (
                <EmptyState
                  icon={<UsersIcon />}
                  title="No churn predictions"
                  description="All users appear to be actively engaged."
                />
              ) : (
                <Card padding="none">
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                          <th className="px-4 py-3">User</th>
                          <th className="px-4 py-3">Churn Probability</th>
                          <th className="px-4 py-3">Risk Level</th>
                          <th className="px-4 py-3">Weeks Inactive</th>
                          <th className="px-4 py-3">Recommendations</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-nova-border">
                        {churnPreds.map((c: any) => (
                          <tr key={c.userId} className="hover:bg-nova-surface-hover transition-colors">
                            <td className="px-4 py-3 text-nova-text">{c.userEmail}</td>
                            <td className="px-4 py-3 font-semibold text-nova-text">
                              {Math.round(c.churnProbability * 100)}%
                            </td>
                            <td className="px-4 py-3">
                              <Badge variant={riskBadge(c.riskLevel)} size="sm">
                                {c.riskLevel}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 text-nova-text-secondary">
                              {c.weeksInactive}
                            </td>
                            <td className="px-4 py-3">
                              {Array.isArray(c.recommendations)
                                ? c.recommendations.map((r: string, i: number) => (
                                    <Badge key={i} variant="info" size="sm" className="mr-1 mb-1">
                                      {r}
                                    </Badge>
                                  ))
                                : <span className="text-xs text-nova-text-muted">—</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </>
          )}

          {/* Collection gaps */}
          {activeTab === 3 && (
            <>
              {gaps.length === 0 ? (
                <EmptyState
                  icon={<RectangleGroupIcon />}
                  title="No collection gaps"
                  description="Your collection appears well-stocked for current demand."
                />
              ) : (
                <Card padding="none">
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                          <th className="px-4 py-3">Category</th>
                          <th className="px-4 py-3">Severity</th>
                          <th className="px-4 py-3">Current Copies</th>
                          <th className="px-4 py-3">Borrow Demand</th>
                          <th className="px-4 py-3">Search Demand</th>
                          <th className="px-4 py-3">Waitlist</th>
                          <th className="px-4 py-3">Suggested</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-nova-border">
                        {gaps.map((g: any, idx: number) => (
                          <tr key={idx} className="hover:bg-nova-surface-hover transition-colors">
                            <td className="px-4 py-3 font-medium text-nova-text">
                              {g.categoryName}
                            </td>
                            <td className="px-4 py-3">
                              <Badge variant={severityBadge(g.gapSeverity)} size="sm">
                                {g.gapSeverity}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 text-nova-text">{g.currentCopies}</td>
                            <td className="px-4 py-3 text-nova-text">{g.borrowDemand}</td>
                            <td className="px-4 py-3 text-nova-text">{g.searchDemand}</td>
                            <td className="px-4 py-3 text-nova-text">{g.waitlistCount}</td>
                            <td className="px-4 py-3 font-semibold text-primary-600">
                              {g.suggestedAcquisitions}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}

/**
 * AdminAnalyticsPage — predictive analytics: AI-powered insights,
 * overdue risk, demand forecasts, churn predictions, collection gap analysis.
 */

import { useLazyQuery, useQuery } from '@apollo/client';
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
  SparklesIcon,
  LightBulbIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import {
  OVERDUE_PREDICTIONS,
  DEMAND_FORECASTS,
  CHURN_PREDICTIONS,
  COLLECTION_GAPS,
  LLM_ANALYTICS,
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

  // LLM Analytics — lazy query so it only fires when user clicks the tab
  const [fetchLLM, { data: llmData, loading: llmLoading, called: llmCalled }] =
    useLazyQuery(LLM_ANALYTICS, { fetchPolicy: 'network-only' });

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
  const llm = llmData?.llmAnalytics;

  // Trigger LLM fetch when switching to AI tab
  const handleTabChange = (idx: number) => {
    setActiveTab(idx);
    if (idx === 0 && !llmCalled) {
      fetchLLM();
    }
  };

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
    { label: 'AI Insights', content: null },
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

      <Tabs tabs={tabs} active={activeTab} onChange={handleTabChange} />

      {/* AI Insights — LLM powered */}
      {activeTab === 0 && (
        <>
          {!llmCalled ? (
            <div className="flex flex-col items-center justify-center py-16 space-y-4">
              <SparklesIcon className="w-16 h-16 text-indigo-400" />
              <h3 className="text-lg font-semibold text-nova-text">AI-Powered Analytics</h3>
              <p className="text-sm text-nova-text-secondary text-center max-w-md">
                Generate comprehensive insights about your library using your configured LLM.
                This analyzes real-time data including borrows, overdue patterns, user engagement,
                and collection coverage.
              </p>
              <button
                onClick={() => fetchLLM()}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 transition-colors"
              >
                <SparklesIcon className="w-5 h-5" />
                Generate AI Analysis
              </button>
            </div>
          ) : llmLoading ? (
            <div className="flex flex-col items-center justify-center py-16 space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
              <p className="text-sm text-nova-text-secondary">
                Analyzing library data with AI... This may take a moment.
              </p>
            </div>
          ) : llm?.error ? (
            <Card>
              <div className="p-6 text-center space-y-3">
                <ExclamationTriangleIcon className="w-12 h-12 text-amber-500 mx-auto" />
                <h3 className="font-semibold text-nova-text">Analysis Failed</h3>
                <p className="text-sm text-red-600 dark:text-red-400">{llm.error}</p>
                <button
                  onClick={() => fetchLLM()}
                  className="mt-2 inline-flex items-center gap-2 rounded-lg bg-gray-100 dark:bg-gray-700 px-4 py-2 text-sm font-medium text-nova-text hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  <ArrowPathIcon className="w-4 h-4" />
                  Retry
                </button>
              </div>
            </Card>
          ) : llm ? (
            <div className="space-y-6">
              {/* Model badge */}
              {llm.modelUsed && (
                <div className="flex items-center gap-2">
                  <Badge variant="info" size="sm">
                    Model: {llm.modelUsed}
                  </Badge>
                  <button
                    onClick={() => fetchLLM()}
                    className="inline-flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                  >
                    <ArrowPathIcon className="w-3.5 h-3.5" />
                    Regenerate
                  </button>
                </div>
              )}

              {/* Executive Summary */}
              {llm.summary && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <SparklesIcon className="w-5 h-5 text-indigo-500" />
                      <h3 className="font-semibold text-nova-text">Executive Summary</h3>
                    </div>
                  </CardHeader>
                  <div className="px-6 pb-5">
                    <p className="text-sm text-nova-text leading-relaxed">{llm.summary}</p>
                  </div>
                </Card>
              )}

              {/* Insight cards grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {llm.overdueInsights && (
                  <Card>
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                        <h3 className="font-semibold text-nova-text">Overdue Risk Analysis</h3>
                      </div>
                    </CardHeader>
                    <div className="px-6 pb-5">
                      <p className="text-sm text-nova-text-secondary leading-relaxed">
                        {llm.overdueInsights}
                      </p>
                    </div>
                  </Card>
                )}

                {llm.demandInsights && (
                  <Card>
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <ArrowTrendingUpIcon className="w-5 h-5 text-emerald-500" />
                        <h3 className="font-semibold text-nova-text">Demand & Trends</h3>
                      </div>
                    </CardHeader>
                    <div className="px-6 pb-5">
                      <p className="text-sm text-nova-text-secondary leading-relaxed">
                        {llm.demandInsights}
                      </p>
                    </div>
                  </Card>
                )}

                {llm.userInsights && (
                  <Card>
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <UsersIcon className="w-5 h-5 text-blue-500" />
                        <h3 className="font-semibold text-nova-text">User Engagement</h3>
                      </div>
                    </CardHeader>
                    <div className="px-6 pb-5">
                      <p className="text-sm text-nova-text-secondary leading-relaxed">
                        {llm.userInsights}
                      </p>
                    </div>
                  </Card>
                )}

                {llm.collectionInsights && (
                  <Card>
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <RectangleGroupIcon className="w-5 h-5 text-purple-500" />
                        <h3 className="font-semibold text-nova-text">Collection Health</h3>
                      </div>
                    </CardHeader>
                    <div className="px-6 pb-5">
                      <p className="text-sm text-nova-text-secondary leading-relaxed">
                        {llm.collectionInsights}
                      </p>
                    </div>
                  </Card>
                )}
              </div>

              {/* Recommendations */}
              {llm.recommendations?.length > 0 && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <LightBulbIcon className="w-5 h-5 text-amber-500" />
                      <h3 className="font-semibold text-nova-text">Actionable Recommendations</h3>
                    </div>
                  </CardHeader>
                  <div className="px-6 pb-5">
                    <ul className="space-y-3">
                      {llm.recommendations.map((rec: string, i: number) => (
                        <li key={i} className="flex items-start gap-3">
                          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 text-xs font-bold flex items-center justify-center mt-0.5">
                            {i + 1}
                          </span>
                          <p className="text-sm text-nova-text leading-relaxed">{rec}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                </Card>
              )}
            </div>
          ) : null}
        </>
      )}

      {(activeTab >= 1 && loading) ? (
        <LoadingOverlay />
      ) : (
        <>
          {/* Overdue risk */}
          {activeTab === 1 && (
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
          {activeTab === 2 && (
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
          {activeTab === 3 && (
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
          {activeTab === 4 && (
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

/**
 * AdminCirculationPage — view all borrows, overdue items, manage circulation.
 * Includes admin actions: force-return, renew, waive fines.
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ArrowUturnLeftIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { ALL_BORROWS, OVERDUE_BORROWS } from '@/graphql/queries/circulation';
import { RETURN_BOOK, RENEW_BORROW } from '@/graphql/mutations/circulation';
import { WAIVE_FINE } from '@/graphql/mutations/circulation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Select } from '@/components/ui/Select';
import { Tabs } from '@/components/ui/Tabs';
import { Pagination } from '@/components/ui/Pagination';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatDate, extractGqlError } from '@/lib/utils';
import { BORROW_STATUS, ITEMS_PER_PAGE } from '@/lib/constants';

const statusOptions = [
  { value: '', label: 'All statuses' },
  ...Object.entries(BORROW_STATUS).map(([key, value]) => ({
    value,
    label: key.charAt(0) + key.slice(1).toLowerCase(),
  })),
];

const statusBadge = (status: string) => {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'neutral'> = {
    ACTIVE: 'info',
    RETURNED: 'success',
    OVERDUE: 'danger',
    LOST: 'neutral',
  };
  return map[status] ?? 'neutral';
};

export default function AdminCirculationPage() {
  useDocumentTitle('Manage Circulation');

  const [activeTab, setActiveTab] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [after, setAfter] = useState<string | null>(null);
  const [returnTarget, setReturnTarget] = useState<{ id: string; title: string } | null>(null);
  const [renewTarget, setRenewTarget] = useState<{ id: string; title: string } | null>(null);

  // All borrows
  const {
    data: borrowsData,
    loading: borrowsLoading,
    refetch: refetchBorrows,
  } = useQuery(ALL_BORROWS, {
    variables: {
      first: ITEMS_PER_PAGE,
      after,
      status: statusFilter || undefined,
    },
    fetchPolicy: 'cache-and-network',
    skip: activeTab !== 0,
  });

  // Overdue borrows
  const {
    data: overdueData,
    loading: overdueLoading,
    refetch: refetchOverdue,
  } = useQuery(OVERDUE_BORROWS, {
    variables: { limit: 50 },
    fetchPolicy: 'cache-and-network',
    skip: activeTab !== 1,
  });

  const edges = (borrowsData?.allBorrows?.edges ?? []).map((e: any) => e.node);
  const pageInfo = borrowsData?.allBorrows?.pageInfo;
  const overdueList = overdueData?.overdueBorrows ?? [];

  // Admin mutations
  const [forceReturn, { loading: returning }] = useMutation(RETURN_BOOK, {
    onCompleted: () => {
      toast.success('Book returned successfully');
      setReturnTarget(null);
      refetchBorrows();
      refetchOverdue();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [renewBorrow, { loading: renewing }] = useMutation(RENEW_BORROW, {
    onCompleted: () => {
      toast.success('Borrow renewed');
      setRenewTarget(null);
      refetchBorrows();
      refetchOverdue();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [waiveFine] = useMutation(WAIVE_FINE, {
    onCompleted: () => {
      toast.success('Fine waived');
      refetchBorrows();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const tabs = [
    { label: 'All Borrows', content: null },
    {
      label: 'Overdue',
      badge: overdueList.length > 0 ? String(overdueList.length) : undefined,
      content: null,
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-nova-text">Circulation</h1>
        <Button
          variant="outline"
          size="sm"
          leftIcon={<ArrowPathIcon className="h-4 w-4" />}
          onClick={() => {
            if (activeTab === 0) refetchBorrows();
            else refetchOverdue();
          }}
        >
          Refresh
        </Button>
      </div>

      <Tabs
        tabs={tabs}
        active={activeTab}
        onChange={(i) => {
          setActiveTab(i);
          setAfter(null);
        }}
      />

      {/* ─── All borrows tab ─────── */}
      {activeTab === 0 && (
        <>
          <div className="flex gap-3">
            <div className="w-44">
              <Select
                value={statusFilter}
                onChange={(v) => {
                  setStatusFilter(v);
                  setAfter(null);
                }}
                options={statusOptions}
              />
            </div>
          </div>

          {borrowsLoading && !borrowsData ? (
            <LoadingOverlay />
          ) : edges.length === 0 ? (
            <EmptyState
              icon={<MagnifyingGlassIcon />}
              title="No borrow records"
              description="Adjust your filters to see results."
            />
          ) : (
            <Card padding="none">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                      <th className="px-4 py-3">Book</th>
                      <th className="px-4 py-3">Borrower</th>
                      <th className="px-4 py-3">Barcode</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Borrowed</th>
                      <th className="px-4 py-3">Due</th>
                      <th className="px-4 py-3">Returned</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-nova-border">
                    {edges.map((b: any) => (
                      <tr key={b.id} className="hover:bg-nova-surface-hover transition-colors">
                        <td className="px-4 py-3 font-medium text-nova-text">
                          {b.bookCopy?.book?.title ?? '—'}
                        </td>
                        <td className="px-4 py-3 text-nova-text-secondary">
                          <span className="block">{b.user?.firstName} {b.user?.lastName}</span>
                          <span className="text-xs text-nova-text-muted">{b.user?.email}</span>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-nova-text-muted">
                          {b.bookCopy?.barcode}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={statusBadge(b.status)} size="sm">
                            {b.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">
                          {formatDate(b.borrowedAt)}
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">
                          {formatDate(b.dueDate)}
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">
                          {b.returnedAt ? formatDate(b.returnedAt) : '—'}
                        </td>
                        <td className="px-4 py-3">
                          {(b.status === 'BORROWED' || b.status === 'OVERDUE') && (
                            <div className="flex items-center gap-1">
                              <Button
                                variant="outline"
                                size="xs"
                                onClick={() => setReturnTarget({ id: b.id, title: b.bookCopy?.book?.title ?? 'this book' })}
                              >
                                Return
                              </Button>
                              <Button
                                variant="ghost"
                                size="xs"
                                onClick={() => setRenewTarget({ id: b.id, title: b.bookCopy?.book?.title ?? 'this borrow' })}
                              >
                                Renew
                              </Button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {pageInfo && (
            <Pagination
              pageInfo={pageInfo}
              onNext={() => setAfter(pageInfo.endCursor)}
            />
          )}
        </>
      )}

      {/* ─── Overdue tab ─────── */}
      {activeTab === 1 && (
        <>
          {overdueLoading ? (
            <LoadingOverlay />
          ) : overdueList.length === 0 ? (
            <EmptyState
              icon={<ExclamationTriangleIcon />}
              title="No overdue borrows"
              description="All items are within their due dates."
            />
          ) : (
            <Card padding="none">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                      <th className="px-4 py-3">Book</th>
                      <th className="px-4 py-3">Borrower</th>
                      <th className="px-4 py-3">Barcode</th>
                      <th className="px-4 py-3">Due Date</th>
                      <th className="px-4 py-3">Days Overdue</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-nova-border">
                    {overdueList.map((b: any) => {
                      const due = new Date(b.dueDate);
                      const daysOverdue = Math.max(
                        0,
                        Math.ceil((Date.now() - due.getTime()) / (1000 * 60 * 60 * 24)),
                      );
                      return (
                        <tr key={b.id} className="hover:bg-nova-surface-hover transition-colors">
                          <td className="px-4 py-3 font-medium text-nova-text">
                            {b.bookCopy?.book?.title}
                          </td>
                          <td className="px-4 py-3">
                            <span className="block text-nova-text-secondary">
                              {b.user?.firstName} {b.user?.lastName}
                            </span>
                            <span className="text-xs text-nova-text-muted">{b.user?.email}</span>
                          </td>
                          <td className="px-4 py-3 font-mono text-xs text-nova-text-muted">
                            {b.bookCopy?.barcode}
                          </td>
                          <td className="px-4 py-3 text-xs text-red-500 font-medium">
                            {formatDate(b.dueDate)}
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant="danger" size="sm">
                              {daysOverdue} day{daysOverdue !== 1 ? 's' : ''}
                            </Badge>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1">
                              <Button
                                variant="outline"
                                size="xs"
                                leftIcon={<ArrowUturnLeftIcon className="h-3.5 w-3.5" />}
                                onClick={() => setReturnTarget({ id: b.id, title: b.bookCopy?.book?.title ?? 'this book' })}
                              >
                                Force Return
                              </Button>
                              <Button
                                variant="ghost"
                                size="xs"
                                onClick={() => setRenewTarget({ id: b.id, title: b.bookCopy?.book?.title ?? 'this borrow' })}
                              >
                                Renew
                              </Button>
                              {b.fine?.id && b.fine.status !== 'PAID' && (
                                <Button
                                  variant="ghost"
                                  size="xs"
                                  onClick={() => waiveFine({ variables: { fineId: b.fine.id } })}
                                >
                                  Waive Fine
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}

      {/* ─── Force-Return confirmation ─── */}
      <ConfirmDialog
        open={!!returnTarget}
        onClose={() => setReturnTarget(null)}
        onConfirm={() => {
          if (returnTarget) forceReturn({ variables: { borrowId: returnTarget.id } });
        }}
        title="Force Return"
        description={`Are you sure you want to mark "${returnTarget?.title}" as returned? This action cannot be undone.`}
        variant="danger"
        confirmLabel="Return"
        loading={returning}
      />

      {/* ─── Renew confirmation ─── */}
      <ConfirmDialog
        open={!!renewTarget}
        onClose={() => setRenewTarget(null)}
        onConfirm={() => {
          if (renewTarget) renewBorrow({ variables: { borrowId: renewTarget.id } });
        }}
        title="Renew Borrow"
        description={`Renew the borrow for "${renewTarget?.title}"? This will extend the due date.`}
        confirmLabel="Renew"
        loading={renewing}
      />
    </div>
  );
}

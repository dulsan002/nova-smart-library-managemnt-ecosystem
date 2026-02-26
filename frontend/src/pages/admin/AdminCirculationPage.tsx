/**
 * AdminCirculationPage — full circulation management dashboard.
 * Tabs: All Borrows · Overdue · Pending Pickups · Fines
 * Admin actions: return, renew, confirm-pickup, pay-fine, waive-fine.
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ArrowUturnLeftIcon,
  CheckCircleIcon,
  BanknotesIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import {
  ALL_BORROWS,
  OVERDUE_BORROWS,
  PENDING_PICKUPS,
  ALL_FINES,
} from '@/graphql/queries/circulation';
import {
  RETURN_BOOK,
  RENEW_BORROW,
  CONFIRM_PICKUP,
  PAY_FINE,
  WAIVE_FINE,
} from '@/graphql/mutations/circulation';
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
import { BORROW_STATUS, FINE_STATUS, ITEMS_PER_PAGE } from '@/lib/constants';

/* ── helpers ── */

const borrowStatusOptions = [
  { value: '', label: 'All statuses' },
  ...Object.entries(BORROW_STATUS).map(([key, value]) => ({
    value,
    label: key.charAt(0) + key.slice(1).toLowerCase(),
  })),
];

const fineStatusOptions = [
  { value: '', label: 'All statuses' },
  ...Object.entries(FINE_STATUS).map(([key, value]) => ({
    value,
    label: key.charAt(0) + key.slice(1).toLowerCase(),
  })),
];

const borrowBadge = (status: string) => {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'neutral'> = {
    ACTIVE: 'info',
    RETURNED: 'success',
    OVERDUE: 'danger',
    LOST: 'neutral',
  };
  return map[status] ?? 'neutral';
};

const fineBadge = (status: string) => {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'neutral'> = {
    PENDING: 'warning',
    PAID: 'success',
    WAIVED: 'neutral',
    OVERDUE: 'danger',
  };
  return map[status] ?? 'neutral';
};

/* ── component ── */

export default function AdminCirculationPage() {
  useDocumentTitle('Manage Circulation');

  const [activeTab, setActiveTab] = useState(0);

  // Borrows state
  const [statusFilter, setStatusFilter] = useState('');
  const [after, setAfter] = useState<string | null>(null);

  // Fines state
  const [fineStatusFilter, setFineStatusFilter] = useState('');

  // Confirmation targets
  const [returnTarget, setReturnTarget] = useState<{ id: string; title: string } | null>(null);
  const [renewTarget, setRenewTarget] = useState<{ id: string; title: string } | null>(null);
  const [pickupTarget, setPickupTarget] = useState<{ id: string; title: string } | null>(null);
  const [payFineTarget, setPayFineTarget] = useState<{ id: string; title: string; amount: number } | null>(null);
  const [waiveFineTarget, setWaiveFineTarget] = useState<{ id: string; title: string } | null>(null);

  /* ── queries ── */

  const {
    data: borrowsData,
    loading: borrowsLoading,
    error: borrowsError,
    refetch: refetchBorrows,
  } = useQuery(ALL_BORROWS, {
    variables: { first: ITEMS_PER_PAGE, after, status: statusFilter || undefined },
    fetchPolicy: 'network-only',
    skip: activeTab !== 0,
    notifyOnNetworkStatusChange: true,
    onError: (e) => console.error('[AllBorrows error]', e.message),
  });

  const {
    data: overdueData,
    loading: overdueLoading,
    error: overdueError,
    refetch: refetchOverdue,
  } = useQuery(OVERDUE_BORROWS, {
    variables: { limit: 50 },
    fetchPolicy: 'network-only',
    skip: activeTab !== 1,
    notifyOnNetworkStatusChange: true,
    onError: (e) => console.error('[OverdueBorrows error]', e.message),
  });

  const {
    data: pickupsData,
    loading: pickupsLoading,
    error: pickupsError,
    refetch: refetchPickups,
  } = useQuery(PENDING_PICKUPS, {
    variables: { limit: 50 },
    fetchPolicy: 'network-only',
    skip: activeTab !== 2,
    notifyOnNetworkStatusChange: true,
    onError: (e) => console.error('[PendingPickups error]', e.message),
  });

  const {
    data: finesData,
    loading: finesLoading,
    error: finesError,
    refetch: refetchFines,
  } = useQuery(ALL_FINES, {
    variables: { status: fineStatusFilter || undefined, limit: 100 },
    fetchPolicy: 'network-only',
    skip: activeTab !== 3,
    notifyOnNetworkStatusChange: true,
    onError: (e) => console.error('[AllFines error]', e.message),
  });

  // Debug: log query results
  useEffect(() => {
    console.log('[Circulation] borrowsData:', borrowsData, 'error:', borrowsError);
  }, [borrowsData, borrowsError]);
  useEffect(() => {
    console.log('[Circulation] overdueData:', overdueData, 'error:', overdueError);
  }, [overdueData, overdueError]);
  useEffect(() => {
    console.log('[Circulation] pickupsData:', pickupsData, 'error:', pickupsError);
  }, [pickupsData, pickupsError]);
  useEffect(() => {
    console.log('[Circulation] finesData:', finesData, 'error:', finesError);
  }, [finesData, finesError]);

  const edges = (borrowsData?.allBorrows?.edges ?? []).map((e: any) => e.node);
  const pageInfo = borrowsData?.allBorrows?.pageInfo;
  const overdueList = overdueData?.overdueBorrows ?? [];
  const pickupsList = pickupsData?.pendingPickups ?? [];
  const finesList = finesData?.allFines ?? [];

  /* ── mutations ── */

  const refetchAll = () => {
    refetchBorrows();
    refetchOverdue();
    refetchPickups();
    refetchFines();
  };

  const [forceReturn, { loading: returning }] = useMutation(RETURN_BOOK, {
    onCompleted: () => {
      toast.success('Book returned successfully');
      setReturnTarget(null);
      refetchAll();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [renewBorrow, { loading: renewing }] = useMutation(RENEW_BORROW, {
    onCompleted: () => {
      toast.success('Borrow renewed');
      setRenewTarget(null);
      refetchAll();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [confirmPickup, { loading: confirming }] = useMutation(CONFIRM_PICKUP, {
    onCompleted: () => {
      toast.success('Pickup confirmed — borrow created');
      setPickupTarget(null);
      refetchAll();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [payFine, { loading: paying }] = useMutation(PAY_FINE, {
    onCompleted: () => {
      toast.success('Fine marked as paid');
      setPayFineTarget(null);
      refetchAll();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [waiveFine, { loading: waiving }] = useMutation(WAIVE_FINE, {
    onCompleted: () => {
      toast.success('Fine waived');
      setWaiveFineTarget(null);
      refetchAll();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  /* ── tabs ── */

  const tabs = [
    { label: 'All Borrows', content: null },
    {
      label: 'Overdue',
      badge: overdueList.length > 0 ? String(overdueList.length) : undefined,
      content: null,
    },
    {
      label: 'Pending Pickups',
      badge: pickupsList.length > 0 ? String(pickupsList.length) : undefined,
      content: null,
    },
    {
      label: 'Fines',
      badge: finesList.filter((f: any) => f.status === 'PENDING' || f.status === 'OVERDUE').length > 0
        ? String(finesList.filter((f: any) => f.status === 'PENDING' || f.status === 'OVERDUE').length)
        : undefined,
      content: null,
    },
  ];

  const handleRefresh = () => {
    if (activeTab === 0) refetchBorrows();
    else if (activeTab === 1) refetchOverdue();
    else if (activeTab === 2) refetchPickups();
    else refetchFines();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-nova-text">Circulation</h1>
        <Button
          variant="outline"
          size="sm"
          leftIcon={<ArrowPathIcon className="h-4 w-4" />}
          onClick={handleRefresh}
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

      {/* Error banner for debugging */}
      {(borrowsError || overdueError || pickupsError || finesError) && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
          <p className="font-medium">Query Error:</p>
          <p>{borrowsError?.message || overdueError?.message || pickupsError?.message || finesError?.message}</p>
          <p className="mt-1 text-xs text-red-500">Try logging out and logging back in to refresh your session.</p>
        </div>
      )}

      {/* ═══════════════════════════════════════════
          TAB 0 — All Borrows
         ═══════════════════════════════════════════ */}
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
                options={borrowStatusOptions}
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
                          <Badge variant={borrowBadge(b.status)} size="sm">
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
                          {(b.status === 'ACTIVE' || b.status === 'OVERDUE') && (
                            <div className="flex items-center gap-1">
                              <Button
                                variant="outline"
                                size="xs"
                                onClick={() =>
                                  setReturnTarget({
                                    id: b.id,
                                    title: b.bookCopy?.book?.title ?? 'this book',
                                  })
                                }
                              >
                                Return
                              </Button>
                              {b.canRenew && (
                                <Button
                                  variant="ghost"
                                  size="xs"
                                  onClick={() =>
                                    setRenewTarget({
                                      id: b.id,
                                      title: b.bookCopy?.book?.title ?? 'this borrow',
                                    })
                                  }
                                >
                                  Renew
                                </Button>
                              )}
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

      {/* ═══════════════════════════════════════════
          TAB 1 — Overdue
         ═══════════════════════════════════════════ */}
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
                      <th className="px-4 py-3">Renewals</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-nova-border">
                    {overdueList.map((b: any) => (
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
                            {b.daysOverdue ?? 0} day{(b.daysOverdue ?? 0) !== 1 ? 's' : ''}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">
                          {b.renewalCount ?? 0}/{b.maxRenewals ?? 3}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <Button
                              variant="outline"
                              size="xs"
                              leftIcon={<ArrowUturnLeftIcon className="h-3.5 w-3.5" />}
                              onClick={() =>
                                setReturnTarget({
                                  id: b.id,
                                  title: b.bookCopy?.book?.title ?? 'this book',
                                })
                              }
                            >
                              Force Return
                            </Button>
                            {b.canRenew && (
                              <Button
                                variant="ghost"
                                size="xs"
                                onClick={() =>
                                  setRenewTarget({
                                    id: b.id,
                                    title: b.bookCopy?.book?.title ?? 'this borrow',
                                  })
                                }
                              >
                                Renew
                              </Button>
                            )}
                          </div>
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

      {/* ═══════════════════════════════════════════
          TAB 2 — Pending Pickups
         ═══════════════════════════════════════════ */}
      {activeTab === 2 && (
        <>
          {pickupsLoading ? (
            <LoadingOverlay />
          ) : pickupsList.length === 0 ? (
            <EmptyState
              icon={<ClockIcon />}
              title="No pending pickups"
              description="No reservations are currently waiting for pickup."
            />
          ) : (
            <Card padding="none">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                      <th className="px-4 py-3">Book</th>
                      <th className="px-4 py-3">Member</th>
                      <th className="px-4 py-3">Assigned Copy</th>
                      <th className="px-4 py-3">Location</th>
                      <th className="px-4 py-3">Expires</th>
                      <th className="px-4 py-3">Hours Left</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-nova-border">
                    {pickupsList.map((r: any) => (
                      <tr key={r.id} className="hover:bg-nova-surface-hover transition-colors">
                        <td className="px-4 py-3 font-medium text-nova-text">
                          {r.book?.title ?? '—'}
                        </td>
                        <td className="px-4 py-3">
                          <span className="block text-nova-text-secondary">
                            {r.user?.firstName} {r.user?.lastName}
                          </span>
                          <span className="text-xs text-nova-text-muted">{r.user?.email}</span>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-nova-text-muted">
                          {r.assignedCopy?.barcode ?? '—'}
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">
                          {r.pickupLocation ?? (r.assignedCopy ? `Floor ${r.assignedCopy.floorNumber}, Shelf ${r.assignedCopy.shelfNumber}` : '—')}
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">
                          {r.expiresAt ? formatDate(r.expiresAt) : '—'}
                        </td>
                        <td className="px-4 py-3">
                          <Badge
                            variant={r.hoursUntilExpiry <= 2 ? 'danger' : r.hoursUntilExpiry <= 6 ? 'warning' : 'info'}
                            size="sm"
                          >
                            {r.hoursUntilExpiry?.toFixed(1) ?? '—'}h
                          </Badge>
                        </td>
                        <td className="px-4 py-3">
                          <Button
                            variant="primary"
                            size="xs"
                            leftIcon={<CheckCircleIcon className="h-3.5 w-3.5" />}
                            onClick={() =>
                              setPickupTarget({
                                id: r.id,
                                title: r.book?.title ?? 'this reservation',
                              })
                            }
                          >
                            Confirm Pickup
                          </Button>
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

      {/* ═══════════════════════════════════════════
          TAB 3 — Fines
         ═══════════════════════════════════════════ */}
      {activeTab === 3 && (
        <>
          <div className="flex gap-3">
            <div className="w-44">
              <Select
                value={fineStatusFilter}
                onChange={(v) => setFineStatusFilter(v)}
                options={fineStatusOptions}
              />
            </div>
          </div>

          {finesLoading && !finesData ? (
            <LoadingOverlay />
          ) : finesList.length === 0 ? (
            <EmptyState
              icon={<BanknotesIcon />}
              title="No fines"
              description="No fines match the selected filter."
            />
          ) : (
            <Card padding="none">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                      <th className="px-4 py-3">Member</th>
                      <th className="px-4 py-3">Book</th>
                      <th className="px-4 py-3">Reason</th>
                      <th className="px-4 py-3">Amount</th>
                      <th className="px-4 py-3">Paid</th>
                      <th className="px-4 py-3">Outstanding</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Issued</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-nova-border">
                    {finesList.map((f: any) => (
                      <tr key={f.id} className="hover:bg-nova-surface-hover transition-colors">
                        <td className="px-4 py-3">
                          <span className="block text-nova-text-secondary">
                            {f.user?.firstName} {f.user?.lastName}
                          </span>
                          <span className="text-xs text-nova-text-muted">{f.user?.email}</span>
                        </td>
                        <td className="px-4 py-3 font-medium text-nova-text">
                          {f.borrowRecord?.bookCopy?.book?.title ?? '—'}
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted capitalize">
                          {f.reason?.toLowerCase().replace(/_/g, ' ') ?? '—'}
                        </td>
                        <td className="px-4 py-3 font-medium text-nova-text">
                          ${Number(f.amount ?? 0).toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">
                          ${Number(f.paidAmount ?? 0).toFixed(2)}
                        </td>
                        <td className="px-4 py-3 font-medium text-red-500">
                          ${Number(f.outstanding ?? 0).toFixed(2)}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={fineBadge(f.status)} size="sm">
                            {f.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">
                          {formatDate(f.issuedAt ?? f.createdAt)}
                        </td>
                        <td className="px-4 py-3">
                          {(f.status === 'PENDING' || f.status === 'OVERDUE') && (
                            <div className="flex items-center gap-1">
                              <Button
                                variant="primary"
                                size="xs"
                                leftIcon={<BanknotesIcon className="h-3.5 w-3.5" />}
                                onClick={() =>
                                  setPayFineTarget({
                                    id: f.id,
                                    title: f.borrowRecord?.bookCopy?.book?.title ?? 'this fine',
                                    amount: f.outstanding ?? f.amount ?? 0,
                                  })
                                }
                              >
                                Pay
                              </Button>
                              <Button
                                variant="ghost"
                                size="xs"
                                onClick={() =>
                                  setWaiveFineTarget({
                                    id: f.id,
                                    title: f.borrowRecord?.bookCopy?.book?.title ?? 'this fine',
                                  })
                                }
                              >
                                Waive
                              </Button>
                            </div>
                          )}
                          {f.status === 'PAID' && (
                            <span className="text-xs text-green-600 font-medium">
                              Paid {f.paidAt ? formatDate(f.paidAt) : ''}
                            </span>
                          )}
                          {f.status === 'WAIVED' && (
                            <span className="text-xs text-nova-text-muted">
                              Waived {f.waivedAt ? formatDate(f.waivedAt) : ''}
                            </span>
                          )}
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

      {/* ═══════════ Confirmation Dialogs ═══════════ */}

      {/* Force-Return */}
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

      {/* Renew */}
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

      {/* Confirm Pickup */}
      <ConfirmDialog
        open={!!pickupTarget}
        onClose={() => setPickupTarget(null)}
        onConfirm={() => {
          if (pickupTarget) confirmPickup({ variables: { reservationId: pickupTarget.id } });
        }}
        title="Confirm Pickup"
        description={`Confirm that the member has picked up "${pickupTarget?.title}"? This will create an active borrow record.`}
        confirmLabel="Confirm Pickup"
        loading={confirming}
      />

      {/* Pay Fine */}
      <ConfirmDialog
        open={!!payFineTarget}
        onClose={() => setPayFineTarget(null)}
        onConfirm={() => {
          if (payFineTarget) payFine({ variables: { fineId: payFineTarget.id, amount: payFineTarget.amount } });
        }}
        title="Record Fine Payment"
        description={`Record payment of $${payFineTarget?.amount?.toFixed(2)} for "${payFineTarget?.title}"? This marks the fine as paid.`}
        confirmLabel="Record Payment"
        loading={paying}
      />

      {/* Waive Fine */}
      <ConfirmDialog
        open={!!waiveFineTarget}
        onClose={() => setWaiveFineTarget(null)}
        onConfirm={() => {
          if (waiveFineTarget) waiveFine({ variables: { fineId: waiveFineTarget.id } });
        }}
        title="Waive Fine"
        description={`Waive the fine for "${waiveFineTarget?.title}"? This cannot be undone.`}
        variant="danger"
        confirmLabel="Waive Fine"
        loading={waiving}
      />
    </div>
  );
}

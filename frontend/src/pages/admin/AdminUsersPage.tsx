/**
 * AdminUsersPage — Premium enterprise user management with 360° panoramic view,
 * detailed edit form, icon action buttons, and rich data visualizations.
 */

import { useState, useCallback } from 'react';
import { useQuery, useLazyQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  MagnifyingGlassIcon,
  UserPlusIcon,
  ShieldCheckIcon,
  ShieldExclamationIcon,
  EyeIcon,
  PencilSquareIcon,
  BookOpenIcon,
  BanknotesIcon,
  ClockIcon,
  TrophyIcon,
  FireIcon,
  ChartBarIcon,
  StarIcon,
  CalendarDaysIcon,
  PhoneIcon,
  IdentificationIcon,
  ArrowPathIcon,
  EllipsisVerticalIcon,
  NoSymbolIcon,
  CheckCircleIcon,
  UserCircleIcon,
  HashtagIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle, useDebounce } from '@/hooks';
import {
  GET_USERS, GET_USER,
  USER_BORROWS, USER_FINES, USER_RESERVATIONS,
  USER_ENGAGEMENT, USER_ACHIEVEMENTS,
} from '@/graphql/queries/admin';
import {
  ACTIVATE_USER, DEACTIVATE_USER, CHANGE_USER_ROLE, ADMIN_UPDATE_USER, ADMIN_CREATE_USER,
} from '@/graphql/mutations/admin';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Avatar } from '@/components/ui/Avatar';
import { Modal, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { Tabs } from '@/components/ui/Tabs';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { Tooltip } from '@/components/ui/Tooltip';
import { Dropdown } from '@/components/ui/Dropdown';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Pagination } from '@/components/ui/Pagination';
import { LoadingOverlay, Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { extractGqlError, formatDate, formatCurrency, kpLevelName } from '@/lib/utils';
import { ROLES, ITEMS_PER_PAGE } from '@/lib/constants';

/* ─── Constants ──────────────────────────── */

const roleOptions = Object.entries(ROLES).map(([key, value]) => ({
  value,
  label: key.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
}));

const statusOptions = [
  { value: '', label: 'All statuses' },
  { value: 'true', label: 'Active' },
  { value: 'false', label: 'Inactive' },
];

const roleFilterOptions = [{ value: '', label: 'All roles' }, ...roleOptions];

const borrowStatusColor = (s: string) => {
  switch (s) { case 'ACTIVE': return 'info'; case 'RETURNED': return 'success'; case 'OVERDUE': case 'LOST': return 'danger'; default: return 'neutral'; }
};
const fineStatusColor = (s: string) => {
  switch (s) { case 'PAID': return 'success'; case 'PENDING': return 'warning'; case 'WAIVED': return 'neutral'; default: return 'danger'; }
};
const reservationStatusColor = (s: string) => {
  switch (s) { case 'PENDING': return 'warning'; case 'READY': return 'success'; case 'FULFILLED': return 'info'; case 'CANCELLED': return 'neutral'; case 'EXPIRED': return 'danger'; default: return 'neutral'; }
};

/* ─── Stat Mini Card ─────────────────────── */
function StatMini({ icon, label, value, color = 'primary' }: { icon: React.ReactNode; label: string; value: string | number; color?: string }) {
  const bgMap: Record<string, string> = {
    primary: 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400',
    success: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    warning: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400',
    danger: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400',
    info: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
  };
  return (
    <div className="flex items-center gap-3 rounded-xl border border-nova-border bg-nova-surface p-4 transition-shadow hover:shadow-md">
      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${bgMap[color] ?? bgMap.primary}`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold text-nova-text">{value}</p>
        <p className="text-xs text-nova-text-muted">{label}</p>
      </div>
    </div>
  );
}

/* ─── Main Component ─────────────────────── */

export default function AdminUsersPage() {
  useDocumentTitle('Manage Users');

  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const debouncedSearch = useDebounce(search, 400);
  const [after, setAfter] = useState<string | null>(null);

  // View & Edit modals
  const [viewUserId, setViewUserId] = useState<string | null>(null);
  const [editUserId, setEditUserId] = useState<string | null>(null);
  const [viewTab, setViewTab] = useState(0);

  // Edit form state
  const [editForm, setEditForm] = useState({
    firstName: '', lastName: '', email: '', phoneNumber: '',
    dateOfBirth: '', institutionId: '', nicNumber: '', avatarUrl: '',
    role: '', isActive: true, isVerified: false,
  });

  // Confirm dialog
  const [confirmAction, setConfirmAction] = useState<{
    type: 'activate' | 'deactivate' | 'roleChange';
    userId: string; userEmail: string; newRole?: string;
  } | null>(null);

  // Create User modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    firstName: '', lastName: '', email: '', password: '',
    phoneNumber: '', dateOfBirth: '', institutionId: '',
    nicNumber: '', role: 'USER',
  });

  /* ─── LIST query ─────────────────────── */
  const { data, loading, refetch } = useQuery(GET_USERS, {
    variables: {
      first: ITEMS_PER_PAGE, after,
      role: roleFilter || undefined,
      isActive: activeFilter ? activeFilter === 'true' : undefined,
      search: debouncedSearch || undefined,
    },
    fetchPolicy: 'cache-and-network',
  });

  const edges = data?.users?.edges ?? [];
  const pageInfo = data?.users?.pageInfo;
  const totalCount = data?.users?.totalCount ?? 0;

  /* ─── 360° VIEW lazy queries ─────────── */
  const [fetchUser, { data: userData, loading: userLoading }] = useLazyQuery(GET_USER, {
    fetchPolicy: 'network-only',
    onError: (e) => toast.error(extractGqlError(e)),
  });
  const [fetchBorrows, { data: borrowsData, loading: borrowsLoading }] = useLazyQuery(USER_BORROWS, {
    fetchPolicy: 'network-only', onError: (e) => toast.error(extractGqlError(e)),
  });
  const [fetchFines, { data: finesData, loading: finesLoading }] = useLazyQuery(USER_FINES, {
    fetchPolicy: 'network-only', onError: (e) => toast.error(extractGqlError(e)),
  });
  const [fetchReservations, { data: reservationsData, loading: reservationsLoading }] = useLazyQuery(USER_RESERVATIONS, {
    fetchPolicy: 'network-only', onError: (e) => toast.error(extractGqlError(e)),
  });
  const [fetchEngagement, { data: engagementData, loading: engagementLoading }] = useLazyQuery(USER_ENGAGEMENT, {
    fetchPolicy: 'network-only', onError: () => {},
  });
  const [fetchAchievements, { data: achievementsData, loading: achievementsLoading }] = useLazyQuery(USER_ACHIEVEMENTS, {
    fetchPolicy: 'network-only', onError: () => {},
  });

  const viewUser = userData?.user;
  const borrows = borrowsData?.userBorrows ?? [];
  const fines = finesData?.userFines ?? [];
  const reservations = reservationsData?.userReservations ?? [];
  const engagement = engagementData?.userEngagement;
  const achievements = achievementsData?.userAchievements ?? [];

  /* ─── Mutations ──────────────────────── */
  const [activateUser] = useMutation(ACTIVATE_USER, {
    onCompleted: () => { toast.success('User activated'); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });
  const [deactivateUser] = useMutation(DEACTIVATE_USER, {
    onCompleted: () => { toast.success('User deactivated'); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });
  const [changeRole] = useMutation(CHANGE_USER_ROLE, {
    onCompleted: () => { toast.success('Role updated'); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });
  const [adminUpdateUser, { loading: updating }] = useMutation(ADMIN_UPDATE_USER, {
    onCompleted: () => { toast.success('User updated'); setEditUserId(null); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });
  const [adminCreateUser, { loading: creatingUser }] = useMutation(ADMIN_CREATE_USER, {
    onCompleted: () => { toast.success('User created successfully'); setShowCreateModal(false); setCreateForm({ firstName: '', lastName: '', email: '', password: '', phoneNumber: '', dateOfBirth: '', institutionId: '', nicNumber: '', role: 'USER' }); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  /* ─── Open 360° View ────────────────── */
  const openView = useCallback((userId: string) => {
    setViewUserId(userId);
    setViewTab(0);
    fetchUser({ variables: { id: userId } });
    fetchBorrows({ variables: { userId, limit: 20 } });
    fetchFines({ variables: { userId } });
    fetchReservations({ variables: { userId } });
    fetchEngagement({ variables: { userId } });
    fetchAchievements({ variables: { userId } });
  }, [fetchUser, fetchBorrows, fetchFines, fetchReservations, fetchEngagement, fetchAchievements]);

  /* ─── Open Edit ─────────────────────── */
  const [fetchEditUser, { loading: editLoading }] = useLazyQuery(GET_USER, {
    fetchPolicy: 'network-only',
    onCompleted: (d: any) => {
      const u = d.user;
      if (u) {
        setEditForm({
          firstName: u.firstName ?? '', lastName: u.lastName ?? '',
          email: u.email ?? '', phoneNumber: u.phoneNumber ?? '',
          dateOfBirth: u.dateOfBirth ?? '', institutionId: u.institutionId ?? '',
          nicNumber: u.nicNumber ?? '',
          avatarUrl: u.avatarUrl ?? '', role: u.role ?? '',
          isActive: u.isActive ?? true, isVerified: u.isVerified ?? false,
        });
      }
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const openEdit = useCallback((userId: string) => {
    setEditUserId(userId);
    fetchEditUser({ variables: { id: userId } });
  }, [fetchEditUser]);

  const handleEditSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!editUserId) return;
    adminUpdateUser({
      variables: {
        userId: editUserId,
        input: {
          firstName: editForm.firstName, lastName: editForm.lastName, email: editForm.email,
          phoneNumber: editForm.phoneNumber || null, dateOfBirth: editForm.dateOfBirth || null,
          institutionId: editForm.institutionId || null, nicNumber: editForm.nicNumber || null,
          avatarUrl: editForm.avatarUrl || null,
          role: editForm.role, isActive: editForm.isActive, isVerified: editForm.isVerified,
        },
      },
    });
  }, [editUserId, editForm, adminUpdateUser]);

  const handleConfirm = useCallback(async () => {
    if (!confirmAction) return;
    const { type, userId, newRole } = confirmAction;
    if (type === 'activate') await activateUser({ variables: { userId } });
    else if (type === 'deactivate') await deactivateUser({ variables: { userId } });
    else if (type === 'roleChange' && newRole) await changeRole({ variables: { userId, newRole } });
    setConfirmAction(null);
  }, [confirmAction, activateUser, deactivateUser, changeRole]);

  /* ─── KP helpers ─────────────────────── */
  const kpDimensions = engagement ? [
    { label: 'Explorer', value: engagement.explorerKp ?? 0, color: 'primary' as const, emoji: '🧭' },
    { label: 'Scholar', value: engagement.scholarKp ?? 0, color: 'accent' as const, emoji: '📚' },
    { label: 'Connector', value: engagement.connectorKp ?? 0, color: 'success' as const, emoji: '🤝' },
    { label: 'Achiever', value: engagement.achieverKp ?? 0, color: 'warning' as const, emoji: '🏅' },
    { label: 'Dedicated', value: engagement.dedicatedKp ?? 0, color: 'danger' as const, emoji: '💪' },
  ] : [];
  const maxKp = Math.max(1, ...kpDimensions.map(d => d.value));

  /* ─── 360° View Tabs ────────────────── */
  const viewTabs = [
    {
      label: 'Profile',
      icon: <IdentificationIcon className="h-4 w-4" />,
      content: userLoading ? <div className="flex justify-center py-12"><Spinner /></div> : viewUser ? (
        <div className="space-y-6">
          {/* Quick stats row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatMini icon={<BookOpenIcon className="h-5 w-5" />} label="Total Borrows" value={borrows.length} color="info" />
            <StatMini icon={<BanknotesIcon className="h-5 w-5" />} label="Active Fines" value={fines.filter((f: any) => f.status === 'PENDING').length} color="danger" />
            <StatMini icon={<TrophyIcon className="h-5 w-5" />} label="Achievements" value={achievements.length} color="warning" />
            <StatMini icon={<StarIcon className="h-5 w-5" />} label="Total KP" value={engagement?.totalKp?.toLocaleString() ?? 0} color="purple" />
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <Card className="p-5 space-y-4">
              <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
                <UserCircleIcon className="h-4 w-4" /> Account Details
              </h4>
              <div className="space-y-3 text-sm">
                {([
                  ['Full Name', viewUser.fullName],
                  ['Email', viewUser.email],
                  ['Phone', viewUser.phoneNumber || '—'],
                  ['Date of Birth', viewUser.dateOfBirth ? formatDate(viewUser.dateOfBirth) : '—'],
                  ['NIC Number', viewUser.nicNumber || '—'],
                  ['Institution ID', viewUser.institutionId || '—'],
                ] as const).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50 last:border-0">
                    <span className="text-nova-text-muted">{k}</span>
                    <span className="font-medium text-nova-text">{v}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card className="p-5 space-y-4">
              <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
                <ShieldCheckIcon className="h-4 w-4" /> System Information
              </h4>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50">
                  <span className="text-nova-text-muted">Role</span>
                  <Badge variant="primary" size="sm">{viewUser.role?.replace(/_/g, ' ')}</Badge>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50">
                  <span className="text-nova-text-muted">Status</span>
                  <Badge variant={viewUser.isActive ? 'success' : 'danger'} size="sm" dot>{viewUser.isActive ? 'Active' : 'Inactive'}</Badge>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50">
                  <span className="text-nova-text-muted">Verified</span>
                  <Badge variant={viewUser.isVerified ? 'success' : 'warning'} size="sm">{viewUser.verificationStatus || (viewUser.isVerified ? 'Verified' : 'Unverified')}</Badge>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50">
                  <span className="text-nova-text-muted">Login Count</span>
                  <span className="font-medium text-nova-text">{viewUser.loginCount ?? 0}</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50">
                  <span className="text-nova-text-muted">Last Login</span>
                  <span className="font-medium text-nova-text">{viewUser.lastLoginAt ? formatDate(viewUser.lastLoginAt) : 'Never'}</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50">
                  <span className="text-nova-text-muted">Joined</span>
                  <span className="font-medium text-nova-text">{formatDate(viewUser.createdAt)}</span>
                </div>
                <div className="flex items-center justify-between py-1.5">
                  <span className="text-nova-text-muted">Updated</span>
                  <span className="font-medium text-nova-text">{formatDate(viewUser.updatedAt)}</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      ) : null,
    },
    {
      label: 'Borrows',
      icon: <BookOpenIcon className="h-4 w-4" />,
      badge: borrows.length || undefined,
      content: borrowsLoading ? <div className="flex justify-center py-12"><Spinner /></div> : borrows.length === 0 ? (
        <EmptyState icon={<BookOpenIcon />} title="No Borrows" description="This user has no borrow records." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-nova-border">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="bg-nova-surface text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                <th className="px-4 py-3">Book</th><th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Borrowed</th><th className="px-4 py-3">Due</th>
                <th className="px-4 py-3">Returned</th><th className="px-4 py-3 text-center">Renewals</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nova-border">
              {borrows.map((b: any) => (
                <tr key={b.id} className="hover:bg-nova-surface-hover transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {b.bookCopy?.book?.coverImageUrl && <img src={b.bookCopy.book.coverImageUrl} alt="" className="h-10 w-7 rounded object-cover shadow-sm" />}
                      <div>
                        <p className="font-medium text-nova-text">{b.bookCopy?.book?.title ?? 'Unknown'}</p>
                        <p className="text-xs text-nova-text-muted font-mono">{b.bookCopy?.barcode}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={borrowStatusColor(b.status)} size="sm">{b.status}</Badge>
                    {b.isOverdue && <Badge variant="danger" size="xs" className="ml-1">{b.daysOverdue}d late</Badge>}
                  </td>
                  <td className="px-4 py-3 text-xs text-nova-text-muted">{formatDate(b.borrowedAt)}</td>
                  <td className="px-4 py-3 text-xs text-nova-text-muted">{formatDate(b.dueDate)}</td>
                  <td className="px-4 py-3 text-xs text-nova-text-muted">{b.returnedAt ? formatDate(b.returnedAt) : '—'}</td>
                  <td className="px-4 py-3 text-center font-medium">{b.renewalCount ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ),
    },
    {
      label: 'Fines',
      icon: <BanknotesIcon className="h-4 w-4" />,
      badge: fines.length || undefined,
      content: finesLoading ? <div className="flex justify-center py-12"><Spinner /></div> : fines.length === 0 ? (
        <EmptyState icon={<BanknotesIcon />} title="No Fines" description="This user has no fines." />
      ) : (
        <div className="space-y-5">
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-xl border border-nova-border bg-nova-surface p-4 text-center">
              <p className="text-2xl font-bold text-nova-text">{formatCurrency(fines.reduce((s: number, f: any) => s + (f.amount ?? 0), 0))}</p>
              <p className="text-xs text-nova-text-muted mt-1">Total Fines</p>
            </div>
            <div className="rounded-xl border border-green-200 dark:border-green-900/50 bg-green-50/50 dark:bg-green-900/10 p-4 text-center">
              <p className="text-2xl font-bold text-green-600">{formatCurrency(fines.reduce((s: number, f: any) => s + (f.paidAmount ?? 0), 0))}</p>
              <p className="text-xs text-nova-text-muted mt-1">Paid</p>
            </div>
            <div className="rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-900/10 p-4 text-center">
              <p className="text-2xl font-bold text-red-600">{formatCurrency(fines.reduce((s: number, f: any) => s + (f.outstanding ?? 0), 0))}</p>
              <p className="text-xs text-nova-text-muted mt-1">Outstanding</p>
            </div>
          </div>
          <div className="overflow-x-auto rounded-xl border border-nova-border">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-nova-surface text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                  <th className="px-4 py-3">Reason</th><th className="px-4 py-3">Book</th>
                  <th className="px-4 py-3">Amount</th><th className="px-4 py-3">Outstanding</th>
                  <th className="px-4 py-3">Status</th><th className="px-4 py-3">Issued</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nova-border">
                {fines.map((f: any) => (
                  <tr key={f.id} className="hover:bg-nova-surface-hover transition-colors">
                    <td className="px-4 py-3 text-nova-text">{f.reason ?? f.description ?? '—'}</td>
                    <td className="px-4 py-3 text-xs text-nova-text-muted">{f.borrowRecord?.bookCopy?.book?.title ?? '—'}</td>
                    <td className="px-4 py-3 font-medium">{formatCurrency(f.amount ?? 0)}</td>
                    <td className="px-4 py-3 font-medium text-red-600">{formatCurrency(f.outstanding ?? 0)}</td>
                    <td className="px-4 py-3"><Badge variant={fineStatusColor(f.status)} size="sm">{f.status}</Badge></td>
                    <td className="px-4 py-3 text-xs text-nova-text-muted">{formatDate(f.issuedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ),
    },
    {
      label: 'Reservations',
      icon: <ClockIcon className="h-4 w-4" />,
      badge: reservations.length || undefined,
      content: reservationsLoading ? <div className="flex justify-center py-12"><Spinner /></div> : reservations.length === 0 ? (
        <EmptyState icon={<ClockIcon />} title="No Reservations" description="This user has no reservations." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-nova-border">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="bg-nova-surface text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                <th className="px-4 py-3">Book</th><th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Queue</th><th className="px-4 py-3">Reserved</th>
                <th className="px-4 py-3">Ready</th><th className="px-4 py-3">Expires</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nova-border">
              {reservations.map((r: any) => (
                <tr key={r.id} className="hover:bg-nova-surface-hover transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {r.book?.coverImageUrl && <img src={r.book.coverImageUrl} alt="" className="h-10 w-7 rounded object-cover shadow-sm" />}
                      <span className="font-medium text-nova-text">{r.book?.title ?? 'Unknown'}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3"><Badge variant={reservationStatusColor(r.status)} size="sm">{r.status}</Badge></td>
                  <td className="px-4 py-3 text-center font-bold text-primary-600">#{r.queuePosition ?? '—'}</td>
                  <td className="px-4 py-3 text-xs text-nova-text-muted">{formatDate(r.reservedAt)}</td>
                  <td className="px-4 py-3 text-xs text-nova-text-muted">{r.readyAt ? formatDate(r.readyAt) : '—'}</td>
                  <td className="px-4 py-3 text-xs text-nova-text-muted">{r.expiresAt ? formatDate(r.expiresAt) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ),
    },
    {
      label: 'Engagement',
      icon: <ChartBarIcon className="h-4 w-4" />,
      content: engagementLoading ? <div className="flex justify-center py-12"><Spinner /></div> : !engagement ? (
        <EmptyState icon={<ChartBarIcon />} title="No Engagement Data" description="No engagement profile found for this user." />
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          <Card className="p-6 space-y-5">
            <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
              <StarIcon className="h-4 w-4" /> Knowledge Points
            </h4>
            <div className="flex items-center gap-5">
              <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 text-white shadow-lg">
                <span className="text-2xl font-black">{engagement.level ?? 0}</span>
                <span className="absolute -bottom-1 -right-1 rounded-full bg-nova-surface px-2 py-0.5 text-[10px] font-bold text-primary-600 shadow ring-2 ring-primary-100 dark:ring-primary-900">{engagement.levelTitle || kpLevelName(engagement.level ?? 0)}</span>
              </div>
              <div>
                <p className="text-3xl font-black text-nova-text">{engagement.totalKp?.toLocaleString() ?? 0}</p>
                <p className="text-sm text-nova-text-muted">Total Knowledge Points</p>
              </div>
            </div>
            <div className="space-y-3 pt-2">
              {kpDimensions.map((dim) => (
                <div key={dim.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-nova-text-muted">{dim.emoji} {dim.label}</span>
                    <span className="font-bold text-nova-text">{dim.value.toLocaleString()}</span>
                  </div>
                  <ProgressBar value={dim.value} max={maxKp} size="sm" color={dim.color} />
                </div>
              ))}
            </div>
          </Card>
          <Card className="p-6 space-y-5">
            <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
              <FireIcon className="h-4 w-4" /> Activity & Rank
            </h4>
            <div className="grid grid-cols-2 gap-4">
              {[
                { icon: <FireIcon className="h-7 w-7 text-orange-500" />, value: engagement.currentStreak ?? 0, label: 'Current Streak', suffix: 'd' },
                { icon: <FireIcon className="h-7 w-7 text-red-500" />, value: engagement.longestStreak ?? 0, label: 'Best Streak', suffix: 'd' },
                { icon: <HashtagIcon className="h-7 w-7 text-purple-500" />, value: `#${engagement.rank ?? '—'}`, label: 'Global Rank', suffix: '' },
                { icon: <GlobeAltIcon className="h-7 w-7 text-blue-500" />, value: engagement.rankPercentile != null ? `Top ${(100 - engagement.rankPercentile).toFixed(0)}%` : '—', label: 'Percentile', suffix: '' },
              ].map((item, i) => (
                <div key={i} className="text-center p-4 rounded-xl bg-nova-surface-hover border border-nova-border/50 transition-shadow hover:shadow-md">
                  <div className="mx-auto mb-2 flex justify-center">{item.icon}</div>
                  <p className="text-2xl font-black text-nova-text">{item.value}{item.suffix}</p>
                  <p className="text-xs text-nova-text-muted">{item.label}</p>
                </div>
              ))}
            </div>
            {engagement.lastActivityDate && (
              <p className="text-xs text-nova-text-muted text-center pt-2">Last activity: {formatDate(engagement.lastActivityDate)}</p>
            )}
          </Card>
        </div>
      ),
    },
    {
      label: 'Achievements',
      icon: <TrophyIcon className="h-4 w-4" />,
      badge: achievements.length || undefined,
      content: achievementsLoading ? <div className="flex justify-center py-12"><Spinner /></div> : achievements.length === 0 ? (
        <EmptyState icon={<TrophyIcon />} title="No Achievements" description="This user hasn't earned any achievements yet." />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {achievements.map((ua: any) => (
            <div key={ua.id} className="group relative overflow-hidden rounded-xl border border-nova-border bg-nova-surface p-4 transition-all hover:shadow-lg hover:border-primary-500/30">
              <div className="flex items-start gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 dark:to-primary-800/30 text-2xl shrink-0 shadow-sm">
                  {ua.achievement?.icon ?? '🏆'}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-bold text-nova-text truncate">{ua.achievement?.name}</p>
                  <p className="text-xs text-nova-text-muted line-clamp-2 mt-0.5">{ua.achievement?.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant={
                      ua.achievement?.rarity === 'LEGENDARY' ? 'kp-diamond' :
                      ua.achievement?.rarity === 'EPIC' ? 'kp-platinum' :
                      ua.achievement?.rarity === 'RARE' ? 'kp-gold' :
                      ua.achievement?.rarity === 'UNCOMMON' ? 'kp-silver' : 'kp-bronze'
                    } size="xs">{ua.achievement?.rarity ?? 'COMMON'}</Badge>
                    <span className="text-xs font-bold text-primary-600">+{ua.kpAwarded ?? ua.achievement?.kpReward ?? 0} KP</span>
                  </div>
                  <p className="text-[10px] text-nova-text-muted mt-1.5">{formatDate(ua.earnedAt)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">Users</h1>
          <p className="text-sm text-nova-text-secondary">{totalCount.toLocaleString()} total users</p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setShowCreateModal(true)} className="gap-2">
            <UserPlusIcon className="h-4 w-4" />
            Create User
          </Button>
          <Button variant="outline" size="sm" leftIcon={<ArrowPathIcon className="h-4 w-4" />} onClick={() => refetch()}>Refresh</Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="w-64">
          <Input placeholder="Search name or email…" value={search} onChange={(e) => { setSearch(e.target.value); setAfter(null); }} leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />} />
        </div>
        <div className="w-44"><Select value={roleFilter} onChange={(v) => { setRoleFilter(v); setAfter(null); }} options={roleFilterOptions} /></div>
        <div className="w-36"><Select value={activeFilter} onChange={(v) => { setActiveFilter(v); setAfter(null); }} options={statusOptions} /></div>
      </div>

      {/* Table */}
      {loading && !data ? <LoadingOverlay /> : edges.length === 0 ? (
        <EmptyState icon={<UserPlusIcon />} title="No users found" description="Try changing your search or filters." />
      ) : (
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-nova-border bg-nova-surface text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Verified</th>
                  <th className="px-4 py-3">Joined</th>
                  <th className="px-4 py-3">Last Login</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nova-border">
                {edges.filter((e: any) => e?.node).map(({ node: user }: any) => (
                  <tr key={user.id} className="hover:bg-nova-surface-hover transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <Avatar name={`${user.firstName} ${user.lastName}`} size="sm" />
                        <div>
                          <p className="font-medium text-nova-text">{user.firstName} {user.lastName}</p>
                          <p className="text-xs text-nova-text-muted">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Select value={user.role} onChange={(newRole) => { if (newRole !== user.role) setConfirmAction({ type: 'roleChange', userId: user.id, userEmail: user.email, newRole }); }} options={roleOptions} />
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={user.isActive ? 'success' : 'danger'} size="sm" dot>{user.isActive ? 'Active' : 'Inactive'}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      {user.isVerified
                        ? <Tooltip content="Verified"><ShieldCheckIcon className="h-5 w-5 text-green-500" /></Tooltip>
                        : <Tooltip content="Not Verified"><ShieldExclamationIcon className="h-5 w-5 text-nova-text-muted" /></Tooltip>}
                    </td>
                    <td className="px-4 py-3 text-xs text-nova-text-muted">{user.createdAt ? new Date(user.createdAt).toLocaleDateString() : '—'}</td>
                    <td className="px-4 py-3 text-xs text-nova-text-muted">{user.lastLoginAt ? new Date(user.lastLoginAt).toLocaleDateString() : 'Never'}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Tooltip content="360° View">
                          <Button variant="ghost" size="sm" onClick={() => openView(user.id)} className="!px-2">
                            <EyeIcon className="h-4 w-4" />
                          </Button>
                        </Tooltip>
                        <Tooltip content="Edit User">
                          <Button variant="ghost" size="sm" onClick={() => openEdit(user.id)} className="!px-2">
                            <PencilSquareIcon className="h-4 w-4" />
                          </Button>
                        </Tooltip>
                        <Dropdown
                          trigger={
                            <Button variant="ghost" size="sm" className="!px-2">
                              <EllipsisVerticalIcon className="h-4 w-4" />
                            </Button>
                          }
                          items={[
                            ...(user.isActive
                              ? [{ label: 'Deactivate', icon: <NoSymbolIcon className="h-4 w-4" />, danger: true, onClick: () => setConfirmAction({ type: 'deactivate', userId: user.id, userEmail: user.email }) }]
                              : [{ label: 'Activate', icon: <CheckCircleIcon className="h-4 w-4" />, onClick: () => setConfirmAction({ type: 'activate', userId: user.id, userEmail: user.email }) }]
                            ),
                          ]}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {pageInfo && <Pagination pageInfo={pageInfo} totalCount={totalCount} currentCount={edges.length} onNext={() => setAfter(pageInfo.endCursor)} />}

      {/* ─── 360° VIEW MODAL ─────────────── */}
      <Modal open={!!viewUserId} onClose={() => setViewUserId(null)} title="" size="full">
        <ModalBody className="!p-0 !space-y-0">
          {/* Gradient Banner */}
          {viewUser && (
            <div className="relative overflow-hidden bg-gradient-to-r from-primary-600 via-primary-500 to-indigo-500 px-8 py-6 text-white">
              <div className="absolute inset-0 opacity-10">
                <svg width="100%" height="100%"><defs><pattern id="dots" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="currentColor" /></pattern></defs><rect width="100%" height="100%" fill="url(#dots)" /></svg>
              </div>
              <div className="relative flex items-center gap-5">
                <div className="ring-4 ring-white/20 rounded-full">
                  <Avatar name={viewUser.fullName ?? viewUser.email} size="xl" src={viewUser.avatarUrl} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-2xl font-bold">{viewUser.fullName}</h3>
                  <p className="text-white/80 text-sm">{viewUser.email}</p>
                  {viewUser.phoneNumber && <p className="text-white/60 text-xs mt-0.5 flex items-center gap-1"><PhoneIcon className="h-3 w-3" />{viewUser.phoneNumber}</p>}
                </div>
                <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
                  <span className="rounded-full bg-white/20 backdrop-blur-sm px-3 py-1 text-xs font-bold">{viewUser.role?.replace(/_/g, ' ')}</span>
                  <span className={`rounded-full px-3 py-1 text-xs font-bold ${viewUser.isActive ? 'bg-green-500/30 text-green-100' : 'bg-red-500/30 text-red-100'}`}>
                    {viewUser.isActive ? '● Active' : '● Inactive'}
                  </span>
                  {viewUser.isVerified && <span className="rounded-full bg-white/20 backdrop-blur-sm px-3 py-1 text-xs font-bold">✓ Verified</span>}
                </div>
              </div>
            </div>
          )}
          <div className="px-6 py-4">
            <Tabs tabs={viewTabs} active={viewTab} onChange={setViewTab} />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => { const id = viewUserId; setViewUserId(null); if (id) openEdit(id); }} leftIcon={<PencilSquareIcon className="h-4 w-4" />}>Edit User</Button>
          <Button onClick={() => setViewUserId(null)}>Close</Button>
        </ModalFooter>
      </Modal>

      {/* ─── EDIT MODAL ──────────────────── */}
      <Modal open={!!editUserId} onClose={() => { setEditUserId(null); setEditForm({ firstName: '', lastName: '', email: '', phoneNumber: '', dateOfBirth: '', institutionId: '', nicNumber: '', avatarUrl: '', role: '', isActive: true, isVerified: false }); }} title="Edit User" size="xl">
        <form onSubmit={handleEditSubmit}>
          <ModalBody>
            {editLoading ? <div className="flex justify-center py-8"><Spinner /></div> : (
              <div className="grid gap-4 sm:grid-cols-2">
                <Input label="First Name" value={editForm.firstName} onChange={(e) => setEditForm({ ...editForm, firstName: e.target.value })} />
                <Input label="Last Name" value={editForm.lastName} onChange={(e) => setEditForm({ ...editForm, lastName: e.target.value })} />
                <div className="sm:col-span-2"><Input label="Email" type="email" value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} /></div>
                <Input label="Phone Number" value={editForm.phoneNumber} onChange={(e) => setEditForm({ ...editForm, phoneNumber: e.target.value })} leftIcon={<PhoneIcon className="h-4 w-4" />} />
                <Input label="Date of Birth" type="date" value={editForm.dateOfBirth} onChange={(e) => setEditForm({ ...editForm, dateOfBirth: e.target.value })} leftIcon={<CalendarDaysIcon className="h-4 w-4" />} />
                <Input label="Institution ID" value={editForm.institutionId} onChange={(e) => setEditForm({ ...editForm, institutionId: e.target.value })} leftIcon={<IdentificationIcon className="h-4 w-4" />} />
                <Input label="NIC Number" value={editForm.nicNumber} onChange={(e) => setEditForm({ ...editForm, nicNumber: e.target.value })} leftIcon={<IdentificationIcon className="h-4 w-4" />} />
                <Input label="Avatar URL" value={editForm.avatarUrl} onChange={(e) => setEditForm({ ...editForm, avatarUrl: e.target.value })} />
                <Select label="Role" value={editForm.role} onChange={(v) => setEditForm({ ...editForm, role: v })} options={roleOptions} />
                <div className="space-y-3 pt-2">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" checked={editForm.isActive} onChange={(e) => setEditForm({ ...editForm, isActive: e.target.checked })} className="h-4 w-4 rounded border-nova-border text-primary-600 focus:ring-primary-500" />
                    <span className="text-sm text-nova-text">Account Active</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" checked={editForm.isVerified} onChange={(e) => setEditForm({ ...editForm, isVerified: e.target.checked })} className="h-4 w-4 rounded border-nova-border text-primary-600 focus:ring-primary-500" />
                    <span className="text-sm text-nova-text">Email Verified</span>
                  </label>
                </div>
              </div>
            )}
          </ModalBody>
          <ModalFooter>
            <Button type="button" variant="outline" onClick={() => setEditUserId(null)}>Cancel</Button>
            <Button type="submit" isLoading={updating}>Save Changes</Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* ─── CREATE USER MODAL ─────────── */}
      <Modal open={showCreateModal} onClose={() => { setShowCreateModal(false); setCreateForm({ firstName: '', lastName: '', email: '', password: '', phoneNumber: '', dateOfBirth: '', institutionId: '', nicNumber: '', role: 'USER' }); }} title="Create New User" size="xl">
        <form onSubmit={(e) => {
          e.preventDefault();
          if (!createForm.email || !createForm.firstName || !createForm.lastName || !createForm.password) {
            toast.error('Please fill in all required fields');
            return;
          }
          adminCreateUser({
            variables: {
              input: {
                email: createForm.email,
                firstName: createForm.firstName,
                lastName: createForm.lastName,
                password: createForm.password,
                phoneNumber: createForm.phoneNumber || null,
                dateOfBirth: createForm.dateOfBirth || null,
                institutionId: createForm.institutionId || null,
                nicNumber: createForm.nicNumber || null,
                role: createForm.role,
              },
            },
          });
        }}>
          <ModalBody>
            <p className="mb-4 text-sm text-nova-text-muted">
              Create a user directly without OCR verification. The user will be marked as verified and active.
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="First Name *" value={createForm.firstName} onChange={(e) => setCreateForm({ ...createForm, firstName: e.target.value })} placeholder="John" />
              <Input label="Last Name *" value={createForm.lastName} onChange={(e) => setCreateForm({ ...createForm, lastName: e.target.value })} placeholder="Doe" />
              <div className="sm:col-span-2">
                <Input label="Email *" type="email" value={createForm.email} onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })} placeholder="john@example.com" />
              </div>
              <div className="sm:col-span-2">
                <Input label="Password *" type="password" value={createForm.password} onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })} placeholder="Minimum 8 characters" />
              </div>
              <Input label="Phone Number" value={createForm.phoneNumber} onChange={(e) => setCreateForm({ ...createForm, phoneNumber: e.target.value })} leftIcon={<PhoneIcon className="h-4 w-4" />} placeholder="+94 77 123 4567" />
              <Input label="Date of Birth" type="date" value={createForm.dateOfBirth} onChange={(e) => setCreateForm({ ...createForm, dateOfBirth: e.target.value })} leftIcon={<CalendarDaysIcon className="h-4 w-4" />} />
              <Input label="Institution ID" value={createForm.institutionId} onChange={(e) => setCreateForm({ ...createForm, institutionId: e.target.value })} leftIcon={<IdentificationIcon className="h-4 w-4" />} placeholder="e.g. STU2024001" />
              <Input label="NIC Number" value={createForm.nicNumber} onChange={(e) => setCreateForm({ ...createForm, nicNumber: e.target.value })} leftIcon={<IdentificationIcon className="h-4 w-4" />} placeholder="e.g. 200012345678" />
              <Select label="Role" value={createForm.role} onChange={(v) => setCreateForm({ ...createForm, role: v })} options={roleOptions} />
            </div>
          </ModalBody>
          <ModalFooter>
            <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button type="submit" isLoading={creatingUser}>Create User</Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* ─── CONFIRM DIALOG ──────────────── */}
      {confirmAction && (
        <ConfirmDialog
          open onClose={() => setConfirmAction(null)} onConfirm={handleConfirm}
          title={confirmAction.type === 'activate' ? 'Activate User' : confirmAction.type === 'deactivate' ? 'Deactivate User' : 'Change User Role'}
          description={confirmAction.type === 'roleChange'
            ? `Change role of ${confirmAction.userEmail} to ${confirmAction.newRole?.replace(/_/g, ' ')}?`
            : `Are you sure you want to ${confirmAction.type} ${confirmAction.userEmail}?`}
          variant={confirmAction.type === 'deactivate' ? 'danger' : 'warning'}
          confirmLabel="Confirm"
        />
      )}
    </div>
  );
}

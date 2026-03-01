/**
 * AdminMembersPage — Full CRUD for library members / patrons / readers.
 *
 * Features:
 * - View all members with search, status & membership-type filters
 * - Create new members (auto-generates membership number)
 * - Edit existing members
 * - Delete members (soft-delete)
 * - 360° panoramic view with gradient banner
 */

import { useState, useCallback } from 'react';
import { useQuery, useLazyQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  PlusCircleIcon,
  PencilSquareIcon,
  TrashIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
  IdentificationIcon,
  PhoneIcon,
  EnvelopeIcon,
  CalendarDaysIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle, useDebounce } from '@/hooks';
import { GET_MEMBERS, GET_MEMBER } from '@/graphql/queries/members';
import { CREATE_MEMBER, UPDATE_MEMBER, DELETE_MEMBER } from '@/graphql/mutations/members';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';
import { Modal, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { Tooltip } from '@/components/ui/Tooltip';
import { Pagination } from '@/components/ui/Pagination';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Tabs } from '@/components/ui/Tabs';
import { extractGqlError, formatDate } from '@/lib/utils';
import { ITEMS_PER_PAGE } from '@/lib/constants';

/* === Helpers === */

const statusColor = (s: string) => {
  switch (s) {
    case 'ACTIVE': return 'success';
    case 'SUSPENDED': return 'warning';
    case 'EXPIRED': return 'neutral';
    case 'REVOKED': return 'danger';
    default: return 'neutral';
  }
};

const membershipTypeLabel = (t: string) => {
  switch (t) {
    case 'STUDENT': return 'Student';
    case 'FACULTY': return 'Faculty';
    case 'STAFF': return 'Staff';
    case 'PUBLIC': return 'Public';
    case 'SENIOR': return 'Senior Citizen';
    case 'CHILD': return 'Child';
    default: return t;
  }
};

const typeOptions = [
  { value: '', label: 'All types' },
  { value: 'STUDENT', label: 'Student' },
  { value: 'FACULTY', label: 'Faculty' },
  { value: 'STAFF', label: 'Staff' },
  { value: 'PUBLIC', label: 'Public' },
  { value: 'SENIOR', label: 'Senior Citizen' },
  { value: 'CHILD', label: 'Child' },
];

const statusOptions = [
  { value: '', label: 'All statuses' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'SUSPENDED', label: 'Suspended' },
  { value: 'EXPIRED', label: 'Expired' },
  { value: 'REVOKED', label: 'Revoked' },
];

const formTypeOptions = typeOptions.filter((o) => o.value !== '');
const formStatusOptions = statusOptions.filter((o) => o.value !== '');

const emptyForm = {
  firstName: '',
  lastName: '',
  email: '',
  phoneNumber: '',
  dateOfBirth: '',
  nicNumber: '',
  address: '',
  membershipType: 'PUBLIC',
  status: 'ACTIVE',
  maxBorrows: '5',
  expiryDate: '',
  emergencyContactName: '',
  emergencyContactPhone: '',
  notes: '',
};

export default function AdminMembersPage() {
  useDocumentTitle('Manage Members');

  const [search, setSearch] = useState('');
  const [after, setAfter] = useState<string | null>(null);
  const [cursorStack, setCursorStack] = useState<string[]>([]);
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const debouncedSearch = useDebounce(search, 400);

  // Modal states
  const [showFormModal, setShowFormModal] = useState(false);
  const [editingMember, setEditingMember] = useState<any | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<any | null>(null);
  const [viewMemberId, setViewMemberId] = useState<string | null>(null);
  const [viewTab, setViewTab] = useState(0);

  // Form state
  const [form, setForm] = useState(emptyForm);

  const setField = (name: string, value: string) => setForm((prev) => ({ ...prev, [name]: value }));

  const { data, loading, refetch } = useQuery(GET_MEMBERS, {
    variables: {
      first: ITEMS_PER_PAGE,
      after,
      status: statusFilter || undefined,
      membershipType: typeFilter || undefined,
      search: debouncedSearch || undefined,
    },
    fetchPolicy: 'cache-and-network',
  });

  const edges = data?.members?.edges ?? [];
  const pageInfo = data?.members?.pageInfo;
  const totalCount = data?.members?.totalCount ?? 0;

  const [fetchMember, { data: memberData, loading: memberLoading }] = useLazyQuery(GET_MEMBER, {
    fetchPolicy: 'network-only',
    onError: (e) => toast.error(extractGqlError(e)),
  });
  const viewMember = memberData?.member;

  const [createMember, { loading: creating }] = useMutation(CREATE_MEMBER, {
    onCompleted: () => { toast.success('Member created'); closeForm(); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [updateMember, { loading: updating }] = useMutation(UPDATE_MEMBER, {
    onCompleted: () => { toast.success('Member updated'); closeForm(); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [deleteMember, { loading: deleting }] = useMutation(DELETE_MEMBER, {
    onCompleted: () => { toast.success('Member deleted'); setDeleteTarget(null); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const openCreate = useCallback(() => {
    setEditingMember(null);
    setForm(emptyForm);
    setShowFormModal(true);
  }, []);

  const openEdit = useCallback((m: any) => {
    setEditingMember(m);
    setForm({
      firstName: m.firstName ?? '',
      lastName: m.lastName ?? '',
      email: m.email ?? '',
      phoneNumber: m.phoneNumber ?? '',
      dateOfBirth: m.dateOfBirth ?? '',
      nicNumber: m.nicNumber ?? '',
      address: m.address ?? '',
      membershipType: m.membershipType ?? 'PUBLIC',
      status: m.status ?? 'ACTIVE',
      maxBorrows: String(m.maxBorrows ?? 5),
      expiryDate: m.expiryDate ?? '',
      emergencyContactName: m.emergencyContactName ?? '',
      emergencyContactPhone: m.emergencyContactPhone ?? '',
      notes: m.notes ?? '',
    });
    setShowFormModal(true);
  }, []);

  const openView = useCallback((id: string) => {
    setViewMemberId(id);
    setViewTab(0);
    fetchMember({ variables: { id } });
  }, [fetchMember]);

  const closeForm = () => {
    setShowFormModal(false);
    setEditingMember(null);
    setForm(emptyForm);
  };

  const handleSubmit = () => {
    if (!form.firstName.trim() || !form.lastName.trim()) {
      toast.error('First name and last name are required');
      return;
    }

    const input: any = {
      firstName: form.firstName.trim(),
      lastName: form.lastName.trim(),
      email: form.email.trim() || undefined,
      phoneNumber: form.phoneNumber.trim() || undefined,
      dateOfBirth: form.dateOfBirth || undefined,
      nicNumber: form.nicNumber.trim() || undefined,
      address: form.address.trim() || undefined,
      membershipType: form.membershipType || undefined,
      maxBorrows: form.maxBorrows ? parseInt(form.maxBorrows, 10) : undefined,
      expiryDate: form.expiryDate || undefined,
      emergencyContactName: form.emergencyContactName.trim() || undefined,
      emergencyContactPhone: form.emergencyContactPhone.trim() || undefined,
      notes: form.notes.trim() || undefined,
    };

    if (editingMember) {
      input.status = form.status || undefined;
      updateMember({ variables: { id: editingMember.id, input } });
    } else {
      createMember({ variables: { input } });
    }
  };

  if (loading && edges.length === 0) return <LoadingOverlay />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">Library Members</h1>
          <p className="text-sm text-nova-text-secondary">
            Manage library patrons, readers and card holders
          </p>
        </div>
        <Button leftIcon={<PlusCircleIcon className="h-4 w-4" />} onClick={openCreate}>
          Add Member
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-100 dark:bg-primary-900/30">
              <UserCircleIcon className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <p className="text-xs font-medium text-nova-text-muted">Total Members</p>
              <p className="text-xl font-bold text-nova-text">{totalCount}</p>
            </div>
          </div>
        </Card>
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-900/30">
              <ShieldCheckIcon className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-xs font-medium text-nova-text-muted">Active</p>
              <p className="text-xl font-bold text-nova-text">
                {edges.filter((e: any) => e?.node?.status === 'ACTIVE').length}
              </p>
            </div>
          </div>
        </Card>
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-yellow-100 dark:bg-yellow-900/30">
              <CalendarDaysIcon className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-xs font-medium text-nova-text-muted">Suspended</p>
              <p className="text-xl font-bold text-nova-text">
                {edges.filter((e: any) => e?.node?.status === 'SUSPENDED').length}
              </p>
            </div>
          </div>
        </Card>
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-100 dark:bg-red-900/30">
              <IdentificationIcon className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-xs font-medium text-nova-text-muted">Expired</p>
              <p className="text-xl font-bold text-nova-text">
                {edges.filter((e: any) => e?.node?.status === 'EXPIRED').length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-nova-text-muted" />
            <input
              type="text"
              placeholder="Search by name, email, phone, ID..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setAfter(null); setCursorStack([]); }}
              className="w-full rounded-lg border border-nova-border bg-nova-surface py-2 pl-9 pr-3 text-sm text-nova-text placeholder:text-nova-text-muted focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-400/30"
            />
          </div>
          <Select
            value={typeFilter}
            onChange={(v) => { setTypeFilter(v); setAfter(null); setCursorStack([]); }}
            options={typeOptions}
          />
          <Select
            value={statusFilter}
            onChange={(v) => { setStatusFilter(v); setAfter(null); setCursorStack([]); }}
            options={statusOptions}
          />
        </div>
      </Card>

      {/* Table */}
      {edges.length === 0 && !loading ? (
        <EmptyState
          icon={<UserCircleIcon className="h-12 w-12" />}
          title="No members found"
          description="Create your first library member to get started."
          action={<Button onClick={openCreate}>Add Member</Button>}
        />
      ) : (
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-nova-border bg-nova-surface-hover/50 text-left text-xs font-medium uppercase tracking-wide text-nova-text-secondary">
                  <th className="px-4 py-3">Member</th>
                  <th className="px-4 py-3">Membership #</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Contact</th>
                  <th className="px-4 py-3">Joined</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nova-border">
                {edges.filter((e: any) => e?.node).map(({ node: m }: any) => (
                  <tr key={m.id} className="hover:bg-nova-surface-hover transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 font-semibold text-xs">
                          {(m.firstName?.[0] ?? '').toUpperCase()}{(m.lastName?.[0] ?? '').toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="truncate font-medium text-nova-text">{m.firstName} {m.lastName}</p>
                          {m.nicNumber && <p className="text-xs text-nova-text-muted">NIC: {m.nicNumber}</p>}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-nova-text-muted">{m.membershipNumber}</td>
                    <td className="px-4 py-3"><Badge variant="neutral" size="sm">{membershipTypeLabel(m.membershipType)}</Badge></td>
                    <td className="px-4 py-3"><Badge variant={statusColor(m.status)} size="sm">{m.status}</Badge></td>
                    <td className="px-4 py-3">
                      <div className="space-y-0.5">
                        {m.email && <p className="text-xs text-nova-text-muted">{m.email}</p>}
                        {m.phoneNumber && <p className="text-xs text-nova-text-muted">{m.phoneNumber}</p>}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-nova-text-secondary text-xs">{formatDate(m.joinedDate)}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Tooltip content="View">
                          <Button variant="ghost" size="sm" onClick={() => openView(m.id)} className="!px-2">
                            <EyeIcon className="h-4 w-4" />
                          </Button>
                        </Tooltip>
                        <Tooltip content="Edit">
                          <Button variant="ghost" size="sm" onClick={() => openEdit(m)} className="!px-2">
                            <PencilSquareIcon className="h-4 w-4" />
                          </Button>
                        </Tooltip>
                        <Tooltip content="Delete">
                          <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(m)} className="!px-2 text-red-500 hover:text-red-600">
                            <TrashIcon className="h-4 w-4" />
                          </Button>
                        </Tooltip>
                      </div>
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
          pageInfo={{ ...pageInfo, hasPreviousPage: cursorStack.length > 0 }}
          totalCount={totalCount}
          currentCount={edges.length}
          onNext={() => {
            setCursorStack((prev) => [...prev, after ?? '']);
            setAfter(pageInfo.endCursor);
          }}
          onPrev={() => {
            const stack = [...cursorStack];
            const prev = stack.pop() ?? '';
            setCursorStack(stack);
            setAfter(prev === '' ? null : prev);
          }}
        />
      )}

      {/* ─── 360° VIEW MODAL ─── */}
      <Modal open={!!viewMemberId} onClose={() => setViewMemberId(null)} title="" size="full">
        <ModalBody className="!p-0 !space-y-0">
          {viewMember && (
            <>
              {/* Gradient banner */}
              <div className="relative overflow-hidden bg-gradient-to-r from-indigo-600 via-purple-500 to-pink-500 px-8 py-6 text-white">
                <div className="absolute inset-0 opacity-10">
                  <svg width="100%" height="100%"><defs><pattern id="member-dots" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="currentColor" /></pattern></defs><rect width="100%" height="100%" fill="url(#member-dots)" /></svg>
                </div>
                <div className="relative flex items-center gap-5">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/20 text-2xl font-bold backdrop-blur">
                    {(viewMember.firstName?.[0] ?? '').toUpperCase()}{(viewMember.lastName?.[0] ?? '').toUpperCase()}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">{viewMember.firstName} {viewMember.lastName}</h2>
                    <p className="text-white/80 text-sm">{viewMember.membershipNumber} · {membershipTypeLabel(viewMember.membershipType)}</p>
                    <div className="mt-1 flex items-center gap-2">
                      <Badge variant={statusColor(viewMember.status)} size="sm">{viewMember.status}</Badge>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="px-6 pt-4 pb-6">
                <Tabs
                  active={viewTab}
                  onChange={setViewTab}
                  tabs={[
                    {
                      label: 'Details',
                      icon: <IdentificationIcon className="h-4 w-4" />,
                      content: (
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                          <InfoTile label="Full Name" value={viewMember.fullName} />
                          <InfoTile label="Membership Number" value={viewMember.membershipNumber} />
                          <InfoTile label="NIC Number" value={viewMember.nicNumber || '—'} />
                          <InfoTile label="Date of Birth" value={formatDate(viewMember.dateOfBirth) || '—'} />
                          <InfoTile label="Membership Type" value={membershipTypeLabel(viewMember.membershipType)} />
                          <InfoTile label="Status" value={viewMember.status} />
                          <InfoTile label="Max Borrows" value={String(viewMember.maxBorrows ?? 5)} />
                          <InfoTile label="Joined" value={formatDate(viewMember.joinedDate)} />
                          <InfoTile label="Expiry Date" value={formatDate(viewMember.expiryDate) || '—'} />
                          {viewMember.user && <InfoTile label="Linked User" value={viewMember.user.email} />}
                        </div>
                      ),
                    },
                    {
                      label: 'Contact',
                      icon: <PhoneIcon className="h-4 w-4" />,
                      content: (
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                          <InfoTile label="Email" value={viewMember.email || '—'} />
                          <InfoTile label="Phone" value={viewMember.phoneNumber || '—'} />
                          <InfoTile label="Address" value={viewMember.address || '—'} />
                          <InfoTile label="Emergency Contact" value={viewMember.emergencyContactName || '—'} />
                          <InfoTile label="Emergency Phone" value={viewMember.emergencyContactPhone || '—'} />
                        </div>
                      ),
                    },
                    {
                      label: 'Notes',
                      icon: <EnvelopeIcon className="h-4 w-4" />,
                      content: (
                        <div className="rounded-lg border border-nova-border bg-nova-surface p-4 text-sm text-nova-text whitespace-pre-wrap">
                          {viewMember.notes || 'No notes.'}
                        </div>
                      ),
                    },
                  ]}
                />
              </div>
            </>
          )}
          {memberLoading && <div className="flex justify-center py-12"><LoadingOverlay /></div>}
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setViewMemberId(null)}>Close</Button>
        </ModalFooter>
      </Modal>

      {/* ─── CREATE / EDIT MODAL ─── */}
      <Modal
        open={showFormModal}
        onClose={closeForm}
        title={editingMember ? 'Edit Member' : 'Add New Member'}
        size="xl"
      >
        <ModalBody>
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input label="First Name *" value={form.firstName} onChange={(e) => setField('firstName', e.target.value)} />
              <Input label="Last Name *" value={form.lastName} onChange={(e) => setField('lastName', e.target.value)} />
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input label="Email" type="email" value={form.email} onChange={(e) => setField('email', e.target.value)} />
              <Input label="Phone Number" value={form.phoneNumber} onChange={(e) => setField('phoneNumber', e.target.value)} />
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input label="Date of Birth" type="date" value={form.dateOfBirth} onChange={(e) => setField('dateOfBirth', e.target.value)} />
              <Input label="NIC Number" value={form.nicNumber} onChange={(e) => setField('nicNumber', e.target.value)} />
            </div>
            <Textarea label="Address" value={form.address} onChange={(e) => setField('address', e.target.value)} rows={2} />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Select label="Membership Type" value={form.membershipType} onChange={(v) => setField('membershipType', v)} options={formTypeOptions} />
              {editingMember && (
                <Select label="Status" value={form.status} onChange={(v) => setField('status', v)} options={formStatusOptions} />
              )}
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input label="Max Borrows" type="number" value={form.maxBorrows} onChange={(e) => setField('maxBorrows', e.target.value)} />
              <Input label="Expiry Date" type="date" value={form.expiryDate} onChange={(e) => setField('expiryDate', e.target.value)} />
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input label="Emergency Contact Name" value={form.emergencyContactName} onChange={(e) => setField('emergencyContactName', e.target.value)} />
              <Input label="Emergency Contact Phone" value={form.emergencyContactPhone} onChange={(e) => setField('emergencyContactPhone', e.target.value)} />
            </div>
            <Textarea label="Notes" value={form.notes} onChange={(e) => setField('notes', e.target.value)} rows={3} />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={closeForm}>Cancel</Button>
          <Button onClick={handleSubmit} isLoading={creating || updating}>{editingMember ? 'Save' : 'Create'}</Button>
        </ModalFooter>
      </Modal>

      {/* ─── DELETE CONFIRMATION ─── */}
      {deleteTarget && (
        <ConfirmDialog
          open
          onClose={() => setDeleteTarget(null)}
          onConfirm={() => deleteMember({ variables: { id: deleteTarget.id } })}
          title="Delete Member"
          description={`Are you sure you want to delete ${deleteTarget.firstName} ${deleteTarget.lastName} (${deleteTarget.membershipNumber})? This action can be undone by an administrator.`}
          variant="danger"
          confirmLabel="Delete"
          loading={deleting}
        />
      )}
    </div>
  );
}

/* Small reusable info-tile */
function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-nova-surface-hover/50 p-3">
      <p className="text-xs font-medium text-nova-text-muted uppercase tracking-wide">{label}</p>
      <p className="mt-1 font-medium text-nova-text">{value}</p>
    </div>
  );
}

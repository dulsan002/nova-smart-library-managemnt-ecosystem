/**
 * AdminRolesPage — RBAC management for Super Admins.
 *
 * Features:
 * - View all role configurations in a table
 * - Create new custom roles
 * - Edit role permissions via a visual matrix (modules × CRUD)
 * - Delete non-system roles
 * - Permission matrix with checkboxes for each module/action
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  PlusCircleIcon,
  PencilSquareIcon,
  TrashIcon,
  ShieldCheckIcon,
  CheckIcon,

} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { GET_ROLE_CONFIGS, GET_AVAILABLE_MODULES } from '@/graphql/queries/roles';
import { CREATE_ROLE_CONFIG, UPDATE_ROLE_CONFIG, DELETE_ROLE_CONFIG } from '@/graphql/mutations/roles';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Modal, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { Tooltip } from '@/components/ui/Tooltip';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { extractGqlError } from '@/lib/utils';

/* ─── Types ─────────────────────────────── */

interface ModuleInfo {
  key: string;
  label: string;
}

interface RoleConfig {
  id: string;
  roleKey: string;
  displayName: string;
  description: string;
  permissions: Record<string, string[]>;
  isSystem: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

const ACTIONS = ['create', 'read', 'update', 'delete'] as const;
type Action = (typeof ACTIONS)[number];

const ACTION_LABELS: Record<Action, string> = {
  create: 'Create',
  read: 'Read',
  update: 'Update',
  delete: 'Delete',
};

const ACTION_COLORS: Record<Action, string> = {
  create: 'bg-green-500',
  read: 'bg-blue-500',
  update: 'bg-amber-500',
  delete: 'bg-red-500',
};

/* ─── Empty Form State ───────────────────── */

const emptyForm = {
  roleKey: '',
  displayName: '',
  description: '',
  permissions: {} as Record<string, string[]>,
};

/* ─── Component ──────────────────────────── */

export default function AdminRolesPage() {
  useDocumentTitle('Roles & Permissions');

  // Data
  const { data, loading, refetch } = useQuery(GET_ROLE_CONFIGS);
  const { data: modulesData } = useQuery(GET_AVAILABLE_MODULES);
  const roles: RoleConfig[] = data?.roleConfigs ?? [];
  const modules: ModuleInfo[] = modulesData?.availableModules ?? [];

  // Mutations
  const [createRole, { loading: creating }] = useMutation(CREATE_ROLE_CONFIG);
  const [updateRole, { loading: updating }] = useMutation(UPDATE_ROLE_CONFIG);
  const [deleteRole] = useMutation(DELETE_ROLE_CONFIG);

  // Modal state
  const [showFormModal, setShowFormModal] = useState(false);
  const [editingRole, setEditingRole] = useState<RoleConfig | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [deleteTarget, setDeleteTarget] = useState<RoleConfig | null>(null);

  // Permission matrix state (for the currently open form)
  const [matrix, setMatrix] = useState<Record<string, Set<Action>>>({});

  /* ─── Open Create ────────────────────── */
  const openCreate = () => {
    setEditingRole(null);
    setForm(emptyForm);
    // Initialize empty matrix
    const m: Record<string, Set<Action>> = {};
    modules.forEach((mod) => { m[mod.key] = new Set(); });
    setMatrix(m);
    setShowFormModal(true);
  };

  /* ─── Open Edit ──────────────────────── */
  const openEdit = (role: RoleConfig) => {
    setEditingRole(role);
    setForm({
      roleKey: role.roleKey,
      displayName: role.displayName,
      description: role.description,
    } as typeof emptyForm);
    // Build matrix from permissions
    const m: Record<string, Set<Action>> = {};
    modules.forEach((mod) => {
      m[mod.key] = new Set((role.permissions[mod.key] ?? []) as Action[]);
    });
    setMatrix(m);
    setShowFormModal(true);
  };

  /* ─── Toggle Permission ──────────────── */
  const togglePerm = (mod: string, action: Action) => {
    setMatrix((prev) => {
      const next = { ...prev };
      const set = new Set(next[mod] ?? []);
      if (set.has(action)) set.delete(action); else set.add(action);
      next[mod] = set;
      return next;
    });
  };

  /* ─── Toggle Entire Module Row ───────── */
  const toggleModuleRow = (mod: string) => {
    setMatrix((prev) => {
      const next = { ...prev };
      const current = next[mod] ?? new Set();
      if (current.size === ACTIONS.length) {
        next[mod] = new Set();
      } else {
        next[mod] = new Set(ACTIONS);
      }
      return next;
    });
  };

  /* ─── Toggle Entire Action Column ────── */
  const toggleActionColumn = (action: Action) => {
    setMatrix((prev) => {
      const allSet = modules.every((m) => (prev[m.key] ?? new Set()).has(action));
      const next = { ...prev };
      modules.forEach((mod) => {
        const set = new Set(next[mod.key] ?? []);
        if (allSet) set.delete(action); else set.add(action);
        next[mod.key] = set;
      });
      return next;
    });
  };

  /* ─── Build permissions from matrix ──── */
  const matrixToPermissions = (): { module: string; actions: string[] }[] => {
    return modules.map((mod) => ({
      module: mod.key,
      actions: Array.from(matrix[mod.key] ?? []),
    }));
  };

  /* ─── Save Role ──────────────────────── */
  const handleSave = async () => {
    const perms = matrixToPermissions();
    try {
      if (editingRole) {
        await updateRole({
          variables: {
            id: editingRole.id,
            displayName: form.displayName,
            description: form.description,
            permissions: perms,
          },
        });
        toast.success('Role updated');
      } else {
        if (!form.roleKey.trim() || !form.displayName.trim()) {
          toast.error('Role key and display name are required');
          return;
        }
        await createRole({
          variables: {
            roleKey: form.roleKey,
            displayName: form.displayName,
            description: form.description,
            permissions: perms,
          },
        });
        toast.success('Role created');
      }
      setShowFormModal(false);
      refetch();
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  };

  /* ─── Delete Role ────────────────────── */
  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteRole({ variables: { id: deleteTarget.id } });
      toast.success('Role deleted');
      setDeleteTarget(null);
      refetch();
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  };

  /* ─── Count total permissions for a role */
  const permCount = (role: RoleConfig) => {
    return Object.values(role.permissions).reduce((sum, acts) => sum + (acts?.length ?? 0), 0);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">Roles &amp; Permissions</h1>
          <p className="mt-1 text-sm text-nova-text-muted">
            Manage role configurations and fine-grained permissions for each module.
          </p>
        </div>
        <Button onClick={openCreate} className="gap-2">
          <PlusCircleIcon className="h-5 w-5" />
          Create Role
        </Button>
      </div>

      {/* Roles Table */}
      <Card className="relative overflow-hidden">
        {loading && <LoadingOverlay />}
        {roles.length === 0 && !loading ? (
          <EmptyState
            icon={<ShieldCheckIcon className="h-12 w-12" />}
            title="No roles configured"
            description="Create your first role to get started."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-nova-border bg-nova-surface">
                  <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-nova-text-muted">Role</th>
                  <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-nova-text-muted">Key</th>
                  <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-nova-text-muted">Permissions</th>
                  <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-nova-text-muted">Type</th>
                  <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-nova-text-muted">Status</th>
                  <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-nova-text-muted text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nova-border">
                {roles.map((role) => (
                  <tr key={role.id} className="hover:bg-nova-surface-hover transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50 dark:bg-primary-900/20">
                          <ShieldCheckIcon className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                        </div>
                        <div>
                          <p className="font-medium text-nova-text">{role.displayName}</p>
                          {role.description && (
                            <p className="text-xs text-nova-text-muted line-clamp-1">{role.description}</p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <code className="rounded bg-nova-surface-hover px-2 py-0.5 text-xs font-mono text-nova-text-secondary">
                        {role.roleKey}
                      </code>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm font-medium text-nova-text">{permCount(role)}</span>
                      <span className="text-xs text-nova-text-muted ml-1">actions</span>
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant={role.isSystem ? 'info' : 'neutral'}>
                        {role.isSystem ? 'System' : 'Custom'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant={role.isActive ? 'success' : 'danger'}>
                        {role.isActive ? 'Active' : 'Inactive'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Tooltip content="Edit permissions">
                          <button
                            onClick={() => openEdit(role)}
                            className="rounded-lg p-2 text-nova-text-muted hover:bg-nova-surface-hover hover:text-primary-600 transition-colors"
                          >
                            <PencilSquareIcon className="h-4 w-4" />
                          </button>
                        </Tooltip>
                        {!role.isSystem && (
                          <Tooltip content="Delete role">
                            <button
                              onClick={() => setDeleteTarget(role)}
                              className="rounded-lg p-2 text-nova-text-muted hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 transition-colors"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </Tooltip>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Create/Edit Modal with Permission Matrix */}
      <Modal
        open={showFormModal}
        onClose={() => setShowFormModal(false)}
        title={editingRole ? `Edit Role — ${editingRole.displayName}` : 'Create New Role'}
        size="xl"
      >
        <ModalBody>
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="Role Key"
                value={form.roleKey}
                onChange={(e) => setForm((f) => ({ ...f, roleKey: e.target.value }))}
                placeholder="e.g. SENIOR_ASSISTANT"
                disabled={!!editingRole}
                className={editingRole ? 'opacity-60' : ''}
              />
              <Input
                label="Display Name"
                value={form.displayName}
                onChange={(e) => setForm((f) => ({ ...f, displayName: e.target.value }))}
                placeholder="e.g. Senior Assistant"
              />
            </div>
            <Textarea
              label="Description"
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="Brief description of what this role is for..."
              rows={2}
            />

            {/* Permission Matrix */}
            <div>
              <h3 className="mb-3 text-sm font-semibold text-nova-text">Permission Matrix</h3>
              <div className="overflow-x-auto rounded-lg border border-nova-border">
                <table className="w-full text-left">
                  <thead>
                    <tr className="bg-nova-surface">
                      <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-nova-text-muted">Module</th>
                      {ACTIONS.map((action) => (
                        <th key={action} className="px-3 py-3 text-center">
                          <button
                            onClick={() => toggleActionColumn(action)}
                            className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-nova-text-muted hover:text-nova-text transition-colors"
                          >
                            <span className={`inline-block h-2 w-2 rounded-full ${ACTION_COLORS[action]}`} />
                            {ACTION_LABELS[action]}
                          </button>
                        </th>
                      ))}
                      <th className="px-3 py-3 text-center text-xs font-semibold uppercase tracking-wider text-nova-text-muted">All</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-nova-border">
                    {modules.map((mod) => {
                      const currentSet = matrix[mod.key] ?? new Set();
                      const allChecked = ACTIONS.every((a) => currentSet.has(a));
                      return (
                        <tr key={mod.key} className="hover:bg-nova-surface-hover/50 transition-colors">
                          <td className="px-4 py-3">
                            <span className="text-sm font-medium text-nova-text">{mod.label}</span>
                          </td>
                          {ACTIONS.map((action) => {
                            const checked = currentSet.has(action);
                            return (
                              <td key={action} className="px-3 py-3 text-center">
                                <button
                                  onClick={() => togglePerm(mod.key, action)}
                                  className={`inline-flex h-7 w-7 items-center justify-center rounded-md border transition-all ${
                                    checked
                                      ? 'border-primary-500 bg-primary-500 text-white shadow-sm'
                                      : 'border-nova-border bg-nova-surface text-transparent hover:border-primary-300 hover:bg-primary-50 dark:hover:bg-primary-900/10'
                                  }`}
                                >
                                  <CheckIcon className="h-4 w-4" />
                                </button>
                              </td>
                            );
                          })}
                          <td className="px-3 py-3 text-center">
                            <button
                              onClick={() => toggleModuleRow(mod.key)}
                              className={`inline-flex h-7 w-7 items-center justify-center rounded-md border transition-all ${
                                allChecked
                                  ? 'border-green-500 bg-green-500 text-white shadow-sm'
                                  : 'border-nova-border bg-nova-surface text-nova-text-muted hover:border-green-300'
                              }`}
                            >
                              <CheckIcon className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="mt-2 text-xs text-nova-text-muted">
                Click column headers to toggle all, or click row "All" buttons to toggle full access per module.
              </p>
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" onClick={() => setShowFormModal(false)}>Cancel</Button>
          <Button onClick={handleSave} isLoading={creating || updating}>
            {editingRole ? 'Save Changes' : 'Create Role'}
          </Button>
        </ModalFooter>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Role"
        description={`Are you sure you want to delete the role "${deleteTarget?.displayName}"? This cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
      />
    </div>
  );
}

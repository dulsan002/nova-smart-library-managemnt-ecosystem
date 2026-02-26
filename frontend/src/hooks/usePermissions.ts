/**
 * usePermissions — hook that fetches the current user's dynamic role
 * permissions (from the RoleConfig model) and provides helpers to check
 * module-level CRUD access.
 *
 * Usage:
 *   const { can, canRead, loading } = usePermissions();
 *   if (canRead('books')) { ... }
 *   if (can('books', 'delete')) { ... }
 */

import { useQuery } from '@apollo/client';
import { MY_PERMISSIONS } from '@/graphql/queries/roles';
import { useAuthStore } from '@/stores/authStore';

export type PermissionAction = 'create' | 'read' | 'update' | 'delete';
export type ModuleKey =
  | 'books'
  | 'authors'
  | 'digital_content'
  | 'users'
  | 'employees'
  | 'circulation'
  | 'assets'
  | 'analytics'
  | 'ai'
  | 'audit'
  | 'settings'
  | 'roles'
  | 'members';

type PermissionsMap = Record<string, PermissionAction[]>;

export function usePermissions() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const { data, loading, error, refetch } = useQuery<{ myPermissions: PermissionsMap }>(
    MY_PERMISSIONS,
    {
      skip: !isAuthenticated,
      fetchPolicy: 'cache-and-network',
    },
  );

  const permissions: PermissionsMap = data?.myPermissions ?? {};

  /** Check if the user has a specific action on a module. */
  const can = (module: ModuleKey, action: PermissionAction): boolean => {
    const actions = permissions[module];
    return Array.isArray(actions) && actions.includes(action);
  };

  /** Shorthand: user can read a module. */
  const canRead = (module: ModuleKey): boolean => can(module, 'read');

  /** Shorthand: user can create in a module. */
  const canCreate = (module: ModuleKey): boolean => can(module, 'create');

  /** Shorthand: user can update in a module. */
  const canUpdate = (module: ModuleKey): boolean => can(module, 'update');

  /** Shorthand: user can delete in a module. */
  const canDelete = (module: ModuleKey): boolean => can(module, 'delete');

  return {
    permissions,
    can,
    canRead,
    canCreate,
    canUpdate,
    canDelete,
    loading,
    error,
    refetch,
  };
}

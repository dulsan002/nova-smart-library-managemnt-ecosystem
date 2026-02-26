/**
 * PermissionGuard — wraps a page / section and blocks rendering if the
 * current user's role does not have the required permission.
 *
 * Usage:
 *   <PermissionGuard module="books" action="read">
 *     <AdminBooksPage />
 *   </PermissionGuard>
 *
 * If `action` is omitted it defaults to "read".
 */

import type { ReactNode } from 'react';
import { usePermissions, type ModuleKey, type PermissionAction } from '@/hooks/usePermissions';
import { ShieldExclamationIcon } from '@heroicons/react/24/outline';

interface PermissionGuardProps {
  module: ModuleKey;
  action?: PermissionAction;
  children: ReactNode;
  /** Optional custom fallback when access is denied. */
  fallback?: ReactNode;
}

export function PermissionGuard({ module, action = 'read', children, fallback }: PermissionGuardProps) {
  const { can, loading } = usePermissions();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  if (!can(module, action)) {
    if (fallback) return <>{fallback}</>;
    return (
      <div className="mx-auto max-w-lg rounded-xl border border-red-200 bg-red-50 p-8 text-center dark:border-red-800 dark:bg-red-900/20">
        <ShieldExclamationIcon className="mx-auto h-12 w-12 text-red-400" />
        <h2 className="mt-4 text-lg font-semibold text-red-700 dark:text-red-300">
          Access Denied
        </h2>
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">
          You do not have permission to access this page. Contact your administrator
          to request the <strong>{action}</strong> permission for the <strong>{module.replace('_', ' ')}</strong> module.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}

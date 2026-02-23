/**
 * AdminRoute — restricts access to admin-role users.
 */

import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { ADMIN_ROLES } from '@/lib/constants';

export function AdminRoute() {
  const user = useAuthStore((s) => s.user);

  if (!user || !ADMIN_ROLES.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

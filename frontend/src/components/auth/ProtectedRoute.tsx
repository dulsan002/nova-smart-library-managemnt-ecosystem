/**
 * ProtectedRoute — redirects unauthenticated users to login.
 * Also activates the auto-logout timer for inactivity protection.
 */

import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { useAutoLogout } from '@/hooks/useAutoLogout';

export function ProtectedRoute() {
  const token = useAuthStore((s) => s.accessToken);
  const location = useLocation();

  // Auto-logout after 30 minutes of inactivity
  useAutoLogout();

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}

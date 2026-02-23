/**
 * useAutoLogout — Logs the user out after a period of inactivity.
 *
 * Listens for mouse / keyboard / touch / scroll events.
 * If none occur within `timeoutMs` (default 30 min), calls `authStore.logout()`
 * and navigates to the login page.
 *
 * Usage:
 *   Place in a component that's always mounted when the user is authenticated,
 *   such as ProtectedRoute or the main layout.
 *
 *   useAutoLogout();             // 30-min default
 *   useAutoLogout(15 * 60_000);  // 15-min custom
 */

import { useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

const DEFAULT_TIMEOUT = 30 * 60 * 1000; // 30 minutes

const ACTIVITY_EVENTS: (keyof WindowEventMap)[] = [
  'mousemove',
  'mousedown',
  'keydown',
  'touchstart',
  'scroll',
];

export function useAutoLogout(timeoutMs: number = DEFAULT_TIMEOUT): void {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleLogout = useCallback(() => {
    logout();
    navigate('/login', { replace: true });
  }, [logout, navigate]);

  const resetTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = setTimeout(handleLogout, timeoutMs);
  }, [handleLogout, timeoutMs]);

  useEffect(() => {
    if (!isAuthenticated) return;

    // Start the timer
    resetTimer();

    // Reset on any user activity
    const handler = () => resetTimer();
    for (const event of ACTIVITY_EVENTS) {
      window.addEventListener(event, handler, { passive: true });
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      for (const event of ACTIVITY_EVENTS) {
        window.removeEventListener(event, handler);
      }
    };
  }, [isAuthenticated, resetTimer]);
}

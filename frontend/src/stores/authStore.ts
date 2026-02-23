/**
 * Auth Store — Zustand store for authentication state.
 *
 * Manages JWT tokens, user data, login/logout, and token refresh.
 * Persists tokens to localStorage for session persistence.
 */

import { create } from 'zustand';
import { apolloClient } from '@/lib/apollo';
import type { UserRole } from '@/lib/constants';

// --- Types ---

export interface AuthUser {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  isVerified: boolean;
  avatarUrl?: string;
}

interface AuthState {
  // State
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setAuth: (user: AuthUser, accessToken: string, refreshToken: string) => void;
  setUser: (user: AuthUser) => void;
  logout: () => void;
  refreshTokens: () => Promise<boolean>;
  hydrate: () => void;
}

const ACCESS_TOKEN_KEY = 'nova_access_token';
const REFRESH_TOKEN_KEY = 'nova_refresh_token';
const USER_KEY = 'nova_user';

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setAuth: (user, accessToken, refreshToken) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({
      user,
      accessToken,
      refreshToken,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  setUser: (user) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ user });
  },

  logout: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    apolloClient.clearStore();
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  refreshTokens: async () => {
    const { refreshToken } = get();
    if (!refreshToken) return false;

    try {
      const { data } = await apolloClient.mutate({
        mutation: (await import('@/graphql/mutations/auth')).REFRESH_TOKEN,
        variables: { refreshToken },
      });

      if (data?.refreshToken?.accessToken) {
        const newAccess = data.refreshToken.accessToken;
        const newRefresh = data.refreshToken.refreshToken || refreshToken;
        localStorage.setItem(ACCESS_TOKEN_KEY, newAccess);
        localStorage.setItem(REFRESH_TOKEN_KEY, newRefresh);
        set({ accessToken: newAccess, refreshToken: newRefresh });
        return true;
      }
      return false;
    } catch {
      get().logout();
      return false;
    }
  },

  hydrate: () => {
    const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    const userJson = localStorage.getItem(USER_KEY);

    if (accessToken && refreshToken && userJson) {
      try {
        const user = JSON.parse(userJson) as AuthUser;
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
          isLoading: false,
        });
        return;
      } catch {
        // JSON parse failed, clear invalid data
      }
    }

    set({ isLoading: false });
  },
}));

// Hydrate on module load
useAuthStore.getState().hydrate();

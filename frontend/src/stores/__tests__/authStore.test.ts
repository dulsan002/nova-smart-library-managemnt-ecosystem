/**
 * Tests for authStore — Zustand store for authentication state.
 *
 * The store imports apolloClient which is difficult to mock at module
 * level, so we focus on state transitions and localStorage interactions
 * while mocking the apollo client.
 */

import { vi } from 'vitest';

// Mock the apollo client BEFORE importing the store
vi.mock('@/lib/apollo', () => ({
  apolloClient: {
    clearStore: vi.fn(),
    mutate: vi.fn(),
  },
}));

// Mock the auth mutation
vi.mock('@/graphql/mutations/auth', () => ({
  REFRESH_TOKEN: 'REFRESH_TOKEN_MOCK',
}));

import { useAuthStore, type AuthUser } from '@/stores/authStore';
import { apolloClient } from '@/lib/apollo';

const mockUser: AuthUser = {
  id: 'u-1',
  email: 'alice@nova.test',
  firstName: 'Alice',
  lastName: 'Smith',
  role: 'MEMBER',
  isVerified: true,
};

// Reset store and localStorage between tests
beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
  useAuthStore.setState({
    accessToken: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false,
    isLoading: false,
  });
});

describe('useAuthStore', () => {
  describe('setAuth', () => {
    it('sets user, tokens, and isAuthenticated', () => {
      useAuthStore.getState().setAuth(mockUser, 'access-123', 'refresh-456');
      const s = useAuthStore.getState();
      expect(s.user).toEqual(mockUser);
      expect(s.accessToken).toBe('access-123');
      expect(s.refreshToken).toBe('refresh-456');
      expect(s.isAuthenticated).toBe(true);
      expect(s.isLoading).toBe(false);
    });

    it('persists tokens and user to localStorage', () => {
      useAuthStore.getState().setAuth(mockUser, 'a', 'r');
      expect(localStorage.getItem('nova_access_token')).toBe('a');
      expect(localStorage.getItem('nova_refresh_token')).toBe('r');
      expect(JSON.parse(localStorage.getItem('nova_user')!)).toEqual(mockUser);
    });
  });

  describe('setUser', () => {
    it('updates user in state and localStorage', () => {
      const updated = { ...mockUser, firstName: 'Bob' };
      useAuthStore.getState().setUser(updated);
      expect(useAuthStore.getState().user).toEqual(updated);
      expect(JSON.parse(localStorage.getItem('nova_user')!).firstName).toBe('Bob');
    });
  });

  describe('logout', () => {
    it('clears state and localStorage', () => {
      useAuthStore.getState().setAuth(mockUser, 'a', 'r');
      useAuthStore.getState().logout();

      const s = useAuthStore.getState();
      expect(s.user).toBeNull();
      expect(s.accessToken).toBeNull();
      expect(s.refreshToken).toBeNull();
      expect(s.isAuthenticated).toBe(false);
      expect(localStorage.getItem('nova_access_token')).toBeNull();
    });

    it('calls apolloClient.clearStore', () => {
      useAuthStore.getState().logout();
      expect(apolloClient.clearStore).toHaveBeenCalled();
    });
  });

  describe('hydrate', () => {
    it('restores state from localStorage', () => {
      localStorage.setItem('nova_access_token', 'tok-a');
      localStorage.setItem('nova_refresh_token', 'tok-r');
      localStorage.setItem('nova_user', JSON.stringify(mockUser));

      useAuthStore.getState().hydrate();
      const s = useAuthStore.getState();
      expect(s.isAuthenticated).toBe(true);
      expect(s.accessToken).toBe('tok-a');
      expect(s.user?.email).toBe('alice@nova.test');
    });

    it('stays unauthenticated when localStorage is empty', () => {
      useAuthStore.getState().hydrate();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().isLoading).toBe(false);
    });

    it('handles corrupted user JSON gracefully', () => {
      localStorage.setItem('nova_access_token', 'tok-a');
      localStorage.setItem('nova_refresh_token', 'tok-r');
      localStorage.setItem('nova_user', '{INVALID');

      useAuthStore.getState().hydrate();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('refreshTokens', () => {
    it('returns false when no refresh token', async () => {
      const result = await useAuthStore.getState().refreshTokens();
      expect(result).toBe(false);
    });

    it('updates tokens on successful refresh', async () => {
      useAuthStore.setState({ refreshToken: 'old-refresh' });
      vi.mocked(apolloClient.mutate).mockResolvedValueOnce({
        data: {
          refreshToken: {
            accessToken: 'new-access',
            refreshToken: 'new-refresh',
          },
        },
      });

      const result = await useAuthStore.getState().refreshTokens();
      expect(result).toBe(true);
      expect(useAuthStore.getState().accessToken).toBe('new-access');
      expect(useAuthStore.getState().refreshToken).toBe('new-refresh');
    });

    it('logs out on refresh failure', async () => {
      useAuthStore.setState({ refreshToken: 'old-refresh', isAuthenticated: true });
      vi.mocked(apolloClient.mutate).mockRejectedValueOnce(new Error('Network'));

      const result = await useAuthStore.getState().refreshTokens();
      expect(result).toBe(false);
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });
});

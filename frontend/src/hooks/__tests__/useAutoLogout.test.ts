/**
 * Tests for useAutoLogout hook.
 */

import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

// Mock apollo client (authStore imports it)
vi.mock('@/lib/apollo', () => ({
  apolloClient: { clearStore: vi.fn(), mutate: vi.fn() },
}));

vi.mock('@/graphql/mutations/auth', () => ({
  REFRESH_TOKEN: 'REFRESH_TOKEN_MOCK',
}));

import { useAuthStore } from '@/stores/authStore';
import { useAutoLogout } from '@/hooks/useAutoLogout';

describe('useAutoLogout', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockNavigate.mockClear();
    useAuthStore.setState({
      accessToken: 'tok',
      refreshToken: 'ref',
      user: {
        id: '1',
        email: 'test@test.com',
        firstName: 'A',
        lastName: 'B',
        role: 'MEMBER',
        isVerified: true,
      },
      isAuthenticated: true,
      isLoading: false,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('does nothing when not authenticated', () => {
    useAuthStore.setState({ isAuthenticated: false });
    renderHook(() => useAutoLogout(1000));
    vi.advanceTimersByTime(2000);
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('logs out and navigates after timeout', () => {
    renderHook(() => useAutoLogout(5000));
    vi.advanceTimersByTime(5000);
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(mockNavigate).toHaveBeenCalledWith('/auth/login', { replace: true });
  });

  it('resets timer on user activity', () => {
    renderHook(() => useAutoLogout(5000));

    // Activity at 3s resets the 5s timer
    vi.advanceTimersByTime(3000);
    act(() => {
      window.dispatchEvent(new Event('mousemove'));
    });

    // At 3s + 4s = 7s total, still should be active (timer reset at 3s)
    vi.advanceTimersByTime(4000);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);

    // At 3s + 5s = 8s total, should now be logged out
    vi.advanceTimersByTime(1000);
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it('cleans up on unmount', () => {
    const { unmount } = renderHook(() => useAutoLogout(5000));
    unmount();
    vi.advanceTimersByTime(10000);
    // Should NOT have logged out since hook was unmounted
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});

/**
 * Tests for uiStore — pure Zustand store for UI state.
 */

import { useUIStore } from '@/stores/uiStore';

// Reset store between tests
beforeEach(() => {
  useUIStore.setState({
    sidebarOpen: false,
    sidebarCollapsed: false,
    commandPaletteOpen: false,
    searchOverlayOpen: false,
  });
});

describe('useUIStore', () => {
  it('has correct initial state', () => {
    const state = useUIStore.getState();
    expect(state.sidebarOpen).toBe(false);
    expect(state.sidebarCollapsed).toBe(false);
    expect(state.commandPaletteOpen).toBe(false);
    expect(state.searchOverlayOpen).toBe(false);
  });

  it('toggleSidebar flips sidebarOpen', () => {
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(true);

    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(false);
  });

  it('setSidebarOpen sets value directly', () => {
    useUIStore.getState().setSidebarOpen(true);
    expect(useUIStore.getState().sidebarOpen).toBe(true);
  });

  it('setSidebarCollapsed persists to localStorage', () => {
    useUIStore.getState().setSidebarCollapsed(true);
    expect(useUIStore.getState().sidebarCollapsed).toBe(true);
    expect(localStorage.getItem('nova-sidebar-collapsed')).toBe('true');
  });

  it('toggleSidebarCollapsed toggles and persists', () => {
    useUIStore.getState().toggleSidebarCollapsed();
    expect(useUIStore.getState().sidebarCollapsed).toBe(true);
    expect(localStorage.getItem('nova-sidebar-collapsed')).toBe('true');

    useUIStore.getState().toggleSidebarCollapsed();
    expect(useUIStore.getState().sidebarCollapsed).toBe(false);
    expect(localStorage.getItem('nova-sidebar-collapsed')).toBe('false');
  });

  it('toggleCommandPalette flips state', () => {
    useUIStore.getState().toggleCommandPalette();
    expect(useUIStore.getState().commandPaletteOpen).toBe(true);

    useUIStore.getState().toggleCommandPalette();
    expect(useUIStore.getState().commandPaletteOpen).toBe(false);
  });

  it('setSearchOverlayOpen sets value', () => {
    useUIStore.getState().setSearchOverlayOpen(true);
    expect(useUIStore.getState().searchOverlayOpen).toBe(true);
  });

  it('toggleSearchOverlay flips state', () => {
    useUIStore.getState().toggleSearchOverlay();
    expect(useUIStore.getState().searchOverlayOpen).toBe(true);

    useUIStore.getState().toggleSearchOverlay();
    expect(useUIStore.getState().searchOverlayOpen).toBe(false);
  });
});

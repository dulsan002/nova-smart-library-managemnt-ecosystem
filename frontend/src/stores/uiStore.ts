/**
 * UI Store — global transient UI state.
 */

import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  commandPaletteOpen: boolean;
  searchOverlayOpen: boolean;

  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebarCollapsed: () => void;
  toggleCommandPalette: () => void;
  setSearchOverlayOpen: (open: boolean) => void;
  toggleSearchOverlay: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  sidebarCollapsed: false,
  commandPaletteOpen: false,
  searchOverlayOpen: false,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setSidebarCollapsed: (collapsed) => {
    localStorage.setItem('nova-sidebar-collapsed', String(collapsed));
    set({ sidebarCollapsed: collapsed });
  },
  toggleSidebarCollapsed: () => {
    const collapsed = !useUIStore.getState().sidebarCollapsed;
    localStorage.setItem('nova-sidebar-collapsed', String(collapsed));
    set({ sidebarCollapsed: collapsed });
  },
  toggleCommandPalette: () => set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
  setSearchOverlayOpen: (open) => set({ searchOverlayOpen: open }),
  toggleSearchOverlay: () => set((s) => ({ searchOverlayOpen: !s.searchOverlayOpen })),
}));

/**
 * Header — top bar with search, theme toggle, notifications, user menu.
 */

import { useNavigate } from 'react-router-dom';
import { useQuery } from '@apollo/client';
import {
  Bars3Icon,
  BellIcon,
  MagnifyingGlassIcon,
  SunIcon,
  MoonIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { useTheme } from '@/lib/theme';
import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';
import { Avatar } from '@/components/ui/Avatar';
import { Dropdown, type DropdownItem } from '@/components/ui/Dropdown';
import { NOTIFICATION_COUNT } from '@/graphql/queries/intelligence';

export function Header() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { toggleSidebar, toggleSearchOverlay } = useUIStore();

  const { data: notifData } = useQuery(NOTIFICATION_COUNT, {
    pollInterval: 30_000,
    fetchPolicy: 'network-only',
  });

  const unreadCount = notifData?.notificationCount?.totalUnread ?? 0;

  const userMenuItems: DropdownItem[] = [
    {
      label: 'My Profile',
      icon: <UserCircleIcon className="h-4 w-4" />,
      onClick: () => navigate('/profile'),
    },
    {
      label: 'Settings',
      icon: <Cog6ToothIcon className="h-4 w-4" />,
      onClick: () => navigate('/profile?tab=settings'),
    },
    {
      label: 'Sign Out',
      icon: <ArrowRightOnRectangleIcon className="h-4 w-4" />,
      onClick: () => {
        logout();
        navigate('/login');
      },
      danger: true,
    },
  ];

  return (
    <header className="flex h-16 items-center justify-between border-b border-nova-border bg-nova-surface px-4 lg:px-6">
      {/* Left: mobile menu + search trigger */}
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="nova-focus rounded-lg p-2 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text lg:hidden"
          aria-label="Toggle sidebar"
        >
          <Bars3Icon className="h-5 w-5" />
        </button>

        {/* Search shortcut */}
        <button
          onClick={toggleSearchOverlay}
          className="nova-focus hidden items-center gap-2 rounded-xl border border-nova-border bg-nova-bg px-4 py-2 text-sm text-nova-text-muted transition-colors hover:border-primary-300 sm:flex"
        >
          <MagnifyingGlassIcon className="h-4 w-4" />
          <span>Search books…</span>
          <kbd className="ml-6 rounded-md border border-nova-border bg-nova-surface px-1.5 py-0.5 text-[10px] font-semibold">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="nova-focus rounded-lg p-2 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text"
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? (
            <SunIcon className="h-5 w-5" />
          ) : (
            <MoonIcon className="h-5 w-5" />
          )}
        </button>

        {/* Notifications */}
        <button
          onClick={() => navigate('/notifications')}
          className="nova-focus relative rounded-lg p-2 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text"
          aria-label="Notifications"
        >
          <BellIcon className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute right-1 top-1 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>

        {/* User menu */}
        {user && (
          <Dropdown
            trigger={
              <button className="nova-focus flex items-center gap-2 rounded-lg p-1.5 transition-colors hover:bg-nova-surface-hover">
                <Avatar
                  name={`${user.firstName} ${user.lastName}`}
                  src={user.avatarUrl}
                  size="sm"
                />
                <span className="hidden text-sm font-medium text-nova-text lg:block">
                  {user.firstName}
                </span>
              </button>
            }
            items={userMenuItems}
          />
        )}
      </div>
    </header>
  );
}

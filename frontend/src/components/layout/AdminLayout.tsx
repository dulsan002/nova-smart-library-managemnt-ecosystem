/**
 * AdminLayout — layout for admin pages with its own sidebar navigation.
 * Sidebar is organized into logical sub-modules for enterprise clarity.
 * Nav items are dynamically filtered based on the user's role permissions.
 */

import { Suspense, useState, useMemo } from 'react';
import { Outlet, NavLink, Navigate, useNavigate } from 'react-router-dom';
import {
  ChartBarSquareIcon,
  UsersIcon,
  BookOpenIcon,
  ArrowPathIcon,
  PresentationChartLineIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  Cog6ToothIcon,
  CubeIcon,
  UserGroupIcon,
  BriefcaseIcon,
  WrenchScrewdriverIcon,
  DocumentTextIcon,
  PencilIcon,
  ChevronDownIcon,
  KeyIcon,
  IdentificationIcon,
  EnvelopeIcon,
  SunIcon,
  MoonIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';
import { useTheme } from '@/lib/theme';
import { ADMIN_ROLES } from '@/lib/constants';
import { LoadingScreen } from '@/components/ui/Spinner';
import { Avatar } from '@/components/ui/Avatar';
import { Dropdown, type DropdownItem } from '@/components/ui/Dropdown';
import { Breadcrumbs } from './Breadcrumbs';
import { SearchOverlay } from './SearchOverlay';
import { usePermissions, type ModuleKey } from '@/hooks/usePermissions';

type NavItem = { label: string; to: string; icon: React.ComponentType<{ className?: string }>; end?: boolean; module?: ModuleKey };
type NavGroup = { title: string; icon: React.ComponentType<{ className?: string }>; items: NavItem[] };

const adminNavGroups: (NavItem | NavGroup)[] = [
  { label: 'Dashboard', to: '/admin', icon: ChartBarSquareIcon, end: true },
  {
    title: 'Catalog',
    icon: BookOpenIcon,
    items: [
      { label: 'Books', to: '/admin/books', icon: BookOpenIcon, module: 'books' },
      { label: 'Authors', to: '/admin/authors', icon: PencilIcon, module: 'authors' },
      { label: 'Digital Content', to: '/admin/digital', icon: DocumentTextIcon, module: 'digital_content' },
    ],
  },
  {
    title: 'People',
    icon: UsersIcon,
    items: [
      { label: 'Users', to: '/admin/users', icon: UsersIcon, module: 'users' },
      { label: 'Members', to: '/admin/members', icon: IdentificationIcon, module: 'members' },
      { label: 'Employees', to: '/admin/employees', icon: UserGroupIcon, module: 'employees' },
      { label: 'Jobs', to: '/admin/jobs', icon: BriefcaseIcon, module: 'employees' },
    ],
  },
  {
    title: 'Operations',
    icon: ArrowPathIcon,
    items: [
      { label: 'Circulation', to: '/admin/circulation', icon: ArrowPathIcon, module: 'circulation' },
      { label: 'Assets', to: '/admin/assets', icon: CubeIcon, module: 'assets' },
    ],
  },
  {
    title: 'Intelligence',
    icon: CpuChipIcon,
    items: [
      { label: 'Analytics', to: '/admin/analytics', icon: PresentationChartLineIcon, module: 'analytics' },
      { label: 'AI Config', to: '/admin/ai-config', icon: Cog6ToothIcon, module: 'ai' },
    ],
  },
  {
    title: 'System',
    icon: ShieldCheckIcon,
    items: [
      { label: 'Roles & Permissions', to: '/admin/roles', icon: KeyIcon, module: 'roles' },
      { label: 'Audit Log', to: '/admin/audit', icon: ShieldCheckIcon, module: 'audit' },
      { label: 'Settings', to: '/admin/settings', icon: WrenchScrewdriverIcon, module: 'settings' },
      { label: 'Email / SMTP', to: '/admin/smtp', icon: EnvelopeIcon, module: 'settings' },
    ],
  },
];

function isGroup(item: NavItem | NavGroup): item is NavGroup {
  return 'items' in item;
}

function NavGroupSection({ group, onNavigate }: { group: NavGroup; onNavigate?: () => void }) {
  const [open, setOpen] = useState(true);
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-[11px] font-semibold uppercase tracking-widest text-nova-text-muted hover:bg-nova-surface-hover transition-colors"
      >
        <span className="flex items-center gap-2">
          <group.icon className="h-4 w-4" />
          {group.title}
        </span>
        <ChevronDownIcon className={cn('h-3.5 w-3.5 transition-transform', !open && '-rotate-90')} />
      </button>
      {open && (
        <ul className="mt-0.5 space-y-0.5 pl-2">
          {group.items.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                      : 'text-nova-text-secondary hover:bg-nova-surface-hover hover:text-nova-text',
                  )
                }
              >
                <item.icon className="h-[18px] w-[18px] flex-shrink-0" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function AdminLayout() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { theme, toggleTheme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { canRead, loading: permLoading } = usePermissions();

  // Filter nav items based on the user's module-level read permissions.
  // Items without a `module` key (e.g. Dashboard) are always shown.
  // Groups whose items are all hidden get removed entirely.
  const filteredNavGroups = useMemo(() => {
    if (permLoading) return []; // wait for permissions to load

    const result: (NavItem | NavGroup)[] = [];
    for (const entry of adminNavGroups) {
      if (isGroup(entry)) {
        const visibleItems = entry.items.filter(
          (item) => !item.module || canRead(item.module),
        );
        if (visibleItems.length > 0) {
          result.push({ ...entry, items: visibleItems });
        }
      } else {
        // Top-level items (Dashboard) — always visible unless they have a module
        if (!entry.module || canRead(entry.module)) {
          result.push(entry);
        }
      }
    }
    return result;
  }, [canRead, permLoading]);

  if (!user || !ADMIN_ROLES.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  const userMenuItems: DropdownItem[] = [
    {
      label: 'My Profile',
      icon: <UserCircleIcon className="h-4 w-4" />,
      onClick: () => navigate('/profile'),
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

  const sidebarContent = (
    <>
      {/* Header */}
      <div className="flex h-16 items-center justify-between border-b border-nova-border px-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white">
            <ShieldCheckIcon className="h-5 w-5" />
          </div>
          <div>
            <span className="text-base font-bold text-nova-text">Admin</span>
            <p className="text-xs text-nova-text-muted">Management Console</p>
          </div>
        </div>
        {/* Close button (mobile only) */}
        <button
          onClick={() => setMobileOpen(false)}
          className="nova-focus rounded-lg p-1.5 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text lg:hidden"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-4 nova-scrollbar">
        <div className="space-y-1">
          {filteredNavGroups.map((entry) =>
            isGroup(entry) ? (
              <NavGroupSection key={entry.title} group={entry} onNavigate={() => setMobileOpen(false)} />
            ) : (
              <NavLink
                key={entry.to}
                to={entry.to}
                end={entry.end}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                      : 'text-nova-text-secondary hover:bg-nova-surface-hover hover:text-nova-text',
                  )
                }
              >
                <entry.icon className="h-5 w-5 flex-shrink-0" />
                {entry.label}
              </NavLink>
            ),
          )}
        </div>
      </nav>

      {/* Bottom user panel */}
      <div className="border-t border-nova-border p-3">
        <div className="flex items-center gap-3 rounded-lg px-2 py-2">
          <Avatar name={`${user.firstName} ${user.lastName}`} src={user.avatarUrl} size="sm" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-nova-text">{user.firstName} {user.lastName}</p>
            <p className="truncate text-xs text-nova-text-muted">{user.role.replace('_', ' ')}</p>
          </div>
        </div>
      </div>
    </>
  );

  return (
    <>
    <SearchOverlay />
    <div className="flex h-screen overflow-hidden bg-nova-bg">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 flex-col border-r border-nova-border bg-nova-surface lg:flex">
        {sidebarContent}
      </aside>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-nova-border bg-nova-surface lg:hidden">
            {sidebarContent}
          </aside>
        </>
      )}

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-16 items-center justify-between border-b border-nova-border bg-nova-surface px-4 lg:px-6">
          {/* Left side */}
          <div className="flex items-center gap-3">
            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileOpen(true)}
              className="nova-focus rounded-lg p-2 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text lg:hidden"
              aria-label="Open sidebar"
            >
              <Bars3Icon className="h-5 w-5" />
            </button>
            <h2 className="text-lg font-semibold text-nova-text lg:hidden">
              Admin
            </h2>
          </div>

          {/* Right side: theme + user dropdown */}
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

            {/* User menu dropdown */}
            <Dropdown
              trigger={
                <button className="nova-focus flex items-center gap-2.5 rounded-lg px-2 py-1.5 transition-colors hover:bg-nova-surface-hover">
                  <Avatar
                    name={`${user.firstName} ${user.lastName}`}
                    src={user.avatarUrl}
                    size="sm"
                  />
                  <div className="hidden text-left lg:block">
                    <p className="text-sm font-medium leading-tight text-nova-text">
                      {user.firstName} {user.lastName}
                    </p>
                    <p className="text-[11px] leading-tight text-nova-text-muted">
                      {user.role.replace('_', ' ')}
                    </p>
                  </div>
                  <ChevronDownIcon className="hidden h-3.5 w-3.5 text-nova-text-muted lg:block" />
                </button>
              }
              items={userMenuItems}
            />
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto nova-scrollbar">
          <div className="px-4 py-6 lg:px-8">
            <Breadcrumbs className="mb-4" />
            <Suspense fallback={<LoadingScreen />}>
              <Outlet />
            </Suspense>
          </div>
        </main>
      </div>
    </div>
    </>
  );
}

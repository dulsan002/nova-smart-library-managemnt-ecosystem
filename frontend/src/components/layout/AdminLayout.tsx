/**
 * AdminLayout — layout for admin pages with its own sidebar navigation.
 * Sidebar is organized into logical sub-modules for enterprise clarity.
 */

import { Suspense, useState } from 'react';
import { Outlet, NavLink, Navigate } from 'react-router-dom';
import {
  ChartBarSquareIcon,
  UsersIcon,
  BookOpenIcon,
  ArrowPathIcon,
  PresentationChartLineIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  ArrowLeftIcon,
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
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';
import { ADMIN_ROLES } from '@/lib/constants';
import { LoadingScreen } from '@/components/ui/Spinner';
import { Breadcrumbs } from './Breadcrumbs';

type NavItem = { label: string; to: string; icon: React.ComponentType<{ className?: string }>; end?: boolean };
type NavGroup = { title: string; icon: React.ComponentType<{ className?: string }>; items: NavItem[] };

const adminNavGroups: (NavItem | NavGroup)[] = [
  { label: 'Dashboard', to: '/admin', icon: ChartBarSquareIcon, end: true },
  {
    title: 'Catalog',
    icon: BookOpenIcon,
    items: [
      { label: 'Books', to: '/admin/books', icon: BookOpenIcon },
      { label: 'Authors', to: '/admin/authors', icon: PencilIcon },
      { label: 'Digital Content', to: '/admin/digital', icon: DocumentTextIcon },
    ],
  },
  {
    title: 'People',
    icon: UsersIcon,
    items: [
      { label: 'Users', to: '/admin/users', icon: UsersIcon },
      { label: 'Members', to: '/admin/members', icon: IdentificationIcon },
      { label: 'Employees', to: '/admin/employees', icon: UserGroupIcon },
      { label: 'Jobs', to: '/admin/jobs', icon: BriefcaseIcon },
    ],
  },
  {
    title: 'Operations',
    icon: ArrowPathIcon,
    items: [
      { label: 'Circulation', to: '/admin/circulation', icon: ArrowPathIcon },
      { label: 'Assets', to: '/admin/assets', icon: CubeIcon },
    ],
  },
  {
    title: 'Intelligence',
    icon: CpuChipIcon,
    items: [
      { label: 'Analytics', to: '/admin/analytics', icon: PresentationChartLineIcon },
      { label: 'AI Models', to: '/admin/ai-models', icon: CpuChipIcon },
      { label: 'AI Config', to: '/admin/ai-config', icon: Cog6ToothIcon },
    ],
  },
  {
    title: 'System',
    icon: ShieldCheckIcon,
    items: [
      { label: 'Roles & Permissions', to: '/admin/roles', icon: KeyIcon },
      { label: 'Audit Log', to: '/admin/audit', icon: ShieldCheckIcon },
      { label: 'Settings', to: '/admin/settings', icon: WrenchScrewdriverIcon },
    ],
  },
];

function isGroup(item: NavItem | NavGroup): item is NavGroup {
  return 'items' in item;
}

function NavGroupSection({ group }: { group: NavGroup }) {
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
  const user = useAuthStore((s) => s.user);

  if (!user || !ADMIN_ROLES.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-nova-bg">
      {/* Admin sidebar */}
      <aside className="hidden w-64 flex-col border-r border-nova-border bg-nova-surface lg:flex">
        {/* Header */}
        <div className="flex h-16 items-center gap-3 border-b border-nova-border px-4">
          <NavLink
            to="/"
            className="nova-focus rounded-lg p-1.5 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text"
            title="Back to App"
          >
            <ArrowLeftIcon className="h-5 w-5" />
          </NavLink>
          <div>
            <span className="text-base font-bold text-nova-text">Admin</span>
            <p className="text-xs text-nova-text-muted">Management Console</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-2 py-4 nova-scrollbar">
          <div className="space-y-1">
            {adminNavGroups.map((entry) =>
              isGroup(entry) ? (
                <NavGroupSection key={entry.title} group={entry} />
              ) : (
                <NavLink
                  key={entry.to}
                  to={entry.to}
                  end={entry.end}
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
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-16 items-center justify-between border-b border-nova-border bg-nova-surface px-4 lg:px-6">
          <div className="flex items-center gap-4">
            <NavLink
              to="/"
              className="nova-focus rounded-lg p-2 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text lg:hidden"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </NavLink>
            <h2 className="text-lg font-semibold text-nova-text lg:hidden">
              Admin Console
            </h2>
          </div>
          <div className="text-sm text-nova-text-secondary">
            Signed in as{' '}
            <span className="font-medium text-nova-text">
              {user.firstName} {user.lastName}
            </span>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto nova-scrollbar">
          <div className="mx-auto max-w-7xl px-4 py-6 lg:px-8">
            <Breadcrumbs className="mb-4" />
            <Suspense fallback={<LoadingScreen />}>
              <Outlet />
            </Suspense>
          </div>
        </main>
      </div>
    </div>
  );
}

/**
 * Sidebar — collapsible navigation sidebar for the main app layout.
 */

import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  BookOpenIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  ClockIcon,
  CurrencyDollarIcon,
  BookmarkIcon,
  TrophyIcon,
  ChartBarIcon,
  SparklesIcon,
  BellIcon,
  LightBulbIcon,
  ChevronLeftIcon,
  Cog6ToothIcon,
  FireIcon,
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores/uiStore';
import { useAuthStore } from '@/stores/authStore';
import { Avatar } from '@/components/ui/Avatar';
import { ADMIN_ROLES } from '@/lib/constants';

interface NavItemDef {
  label: string;
  to: string;
  icon: React.ComponentType<{ className?: string }>;
}

const mainNav: NavItemDef[] = [
  { label: 'Dashboard', to: '/', icon: HomeIcon },
  { label: 'Catalog', to: '/catalog', icon: BookOpenIcon },
  { label: 'Search', to: '/search', icon: MagnifyingGlassIcon },
];

const circulationNav: NavItemDef[] = [
  { label: 'My Borrows', to: '/borrows', icon: ArrowPathIcon },
  { label: 'Reservations', to: '/reservations', icon: ClockIcon },
  { label: 'Fines', to: '/fines', icon: CurrencyDollarIcon },
];

const digitalNav: NavItemDef[] = [
  { label: 'Digital Library', to: '/library', icon: BookmarkIcon },
];

const engagementNav: NavItemDef[] = [
  { label: 'KP Center', to: '/kp-center', icon: FireIcon },
  { label: 'Achievements', to: '/achievements', icon: TrophyIcon },
  { label: 'Leaderboard', to: '/leaderboard', icon: ChartBarIcon },
];

const intelligenceNav: NavItemDef[] = [
  { label: 'Recommendations', to: '/recommendations', icon: SparklesIcon },
  { label: 'Notifications', to: '/notifications', icon: BellIcon },
  { label: 'Insights', to: '/insights', icon: LightBulbIcon },
];

function NavSection({
  title,
  items,
  collapsed,
}: {
  title: string;
  items: NavItemDef[];
  collapsed: boolean;
}) {
  return (
    <div>
      {!collapsed && (
        <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-widest text-nova-text-muted">
          {title}
        </p>
      )}
      <ul className="space-y-0.5">
        {items.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                cn(
                  'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                    : 'text-nova-text-secondary hover:bg-nova-surface-hover hover:text-nova-text',
                  collapsed && 'justify-center px-2',
                )
              }
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebarCollapsed } = useUIStore();
  const user = useAuthStore((s) => s.user);

  return (
    <aside
      className={cn(
        'flex h-screen flex-col border-r border-nova-border bg-nova-surface transition-all duration-200',
        sidebarCollapsed ? 'w-[68px]' : 'w-64',
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between border-b border-nova-border px-4">
        {!sidebarCollapsed && (
          <span className="text-lg font-bold text-primary-600">
            Nova<span className="text-accent-500">Lib</span>
          </span>
        )}
        <button
          onClick={toggleSidebarCollapsed}
          className="nova-focus rounded-lg p-1.5 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text"
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <ChevronLeftIcon
            className={cn(
              'h-5 w-5 transition-transform',
              sidebarCollapsed && 'rotate-180',
            )}
          />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-5 overflow-y-auto px-2 py-4 nova-scrollbar">
        <NavSection title="Main" items={mainNav} collapsed={sidebarCollapsed} />
        <NavSection title="Circulation" items={circulationNav} collapsed={sidebarCollapsed} />
        <NavSection title="Digital" items={digitalNav} collapsed={sidebarCollapsed} />
        <NavSection title="Engagement" items={engagementNav} collapsed={sidebarCollapsed} />
        <NavSection title="Intelligence" items={intelligenceNav} collapsed={sidebarCollapsed} />
      </nav>

      {/* User panel */}
      {user && (
        <div className="border-t border-nova-border p-3">
          <NavLink
            to="/profile"
            className={cn(
              'flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-nova-surface-hover',
              sidebarCollapsed && 'justify-center',
            )}
          >
            <Avatar
              name={`${user.firstName} ${user.lastName}`}
              src={user.avatarUrl}
              size="sm"
            />
            {!sidebarCollapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-nova-text">
                  {user.firstName} {user.lastName}
                </p>
                <p className="truncate text-xs text-nova-text-muted">
                  {user.role}
                </p>
              </div>
            )}
          </NavLink>

          {/* Admin link */}
          {user.role && ADMIN_ROLES.includes(user.role) && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                cn(
                  'mt-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-accent-50 text-accent-700 dark:bg-accent-900/20 dark:text-accent-300'
                    : 'text-nova-text-secondary hover:bg-nova-surface-hover hover:text-nova-text',
                  sidebarCollapsed && 'justify-center px-2',
                )
              }
              title={sidebarCollapsed ? 'Admin Panel' : undefined}
            >
              <Cog6ToothIcon className="h-5 w-5" />
              {!sidebarCollapsed && <span>Admin Panel</span>}
            </NavLink>
          )}
        </div>
      )}
    </aside>
  );
}

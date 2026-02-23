/**
 * Breadcrumbs — auto-generated from current route path.
 */

import { Link, useLocation } from 'react-router-dom';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/20/solid';
import { cn, capitalize } from '@/lib/utils';

const routeLabels: Record<string, string> = {
  catalog: 'Catalog',
  search: 'Search',
  borrows: 'My Borrows',
  reservations: 'Reservations',
  fines: 'Fines',
  library: 'My Library',
  reader: 'Reader',
  profile: 'Profile',
  achievements: 'Achievements',
  leaderboard: 'Leaderboard',
  recommendations: 'Recommendations',
  notifications: 'Notifications',
  insights: 'Reading Insights',
  admin: 'Admin',
  users: 'Users',
  books: 'Books',
  circulation: 'Circulation',
  analytics: 'Analytics',
  'ai-models': 'AI Models',
  audit: 'Audit Log',
  dashboard: 'Dashboard',
};

interface BreadcrumbItem {
  label: string;
  href: string;
}

function buildBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split('/').filter(Boolean);
  const crumbs: BreadcrumbItem[] = [];

  let path = '';
  for (const seg of segments) {
    path += `/${seg}`;
    const label = routeLabels[seg] || capitalize(seg.replace(/-/g, ' '));
    crumbs.push({ label, href: path });
  }

  return crumbs;
}

export function Breadcrumbs({ className }: { className?: string }) {
  const location = useLocation();
  const crumbs = buildBreadcrumbs(location.pathname);

  if (crumbs.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className={cn('text-sm', className)}>
      <ol className="flex items-center gap-1.5">
        <li>
          <Link
            to="/"
            className="nova-focus rounded-md text-nova-text-muted transition-colors hover:text-nova-text"
          >
            <HomeIcon className="h-4 w-4" />
            <span className="sr-only">Home</span>
          </Link>
        </li>
        {crumbs.map((crumb, idx) => {
          const isLast = idx === crumbs.length - 1;
          return (
            <li key={crumb.href} className="flex items-center gap-1.5">
              <ChevronRightIcon className="h-3.5 w-3.5 text-nova-text-muted" />
              {isLast ? (
                <span className="font-medium text-nova-text" aria-current="page">
                  {crumb.label}
                </span>
              ) : (
                <Link
                  to={crumb.href}
                  className="nova-focus rounded-md text-nova-text-muted transition-colors hover:text-nova-text"
                >
                  {crumb.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

/**
 * DataTable — sortable, filterable table for admin views.
 */

import { useState, type ReactNode } from 'react';
import {
  ChevronUpIcon,
  ChevronDownIcon,
  ChevronUpDownIcon,
} from '@heroicons/react/20/solid';
import { cn } from '@/lib/utils';
import { SkeletonLine } from './Spinner';

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  className?: string;
  render: (row: T, index: number) => ReactNode;
}

type SortDir = 'asc' | 'desc' | null;

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  loading?: boolean;
  skeletonRows?: number;
  emptyMessage?: string;
  onSort?: (key: string, direction: SortDir) => void;
  className?: string;
  stickyHeader?: boolean;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  loading = false,
  skeletonRows = 5,
  emptyMessage = 'No data found',
  onSort,
  className,
  stickyHeader = false,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);

  function handleSort(key: string) {
    let next: SortDir;
    if (sortKey !== key) {
      next = 'asc';
    } else if (sortDir === 'asc') {
      next = 'desc';
    } else {
      next = null;
    }
    setSortKey(next ? key : null);
    setSortDir(next);
    onSort?.(key, next);
  }

  return (
    <div className={cn('overflow-x-auto rounded-xl border border-nova-border', className)}>
      <table className="min-w-full divide-y divide-nova-border">
        <thead className={cn('bg-nova-surface', stickyHeader && 'sticky top-0 z-10')}>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={cn(
                  'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-nova-text-secondary',
                  col.sortable && 'cursor-pointer select-none',
                  col.className,
                )}
                onClick={col.sortable ? () => handleSort(col.key) : undefined}
              >
                <span className="inline-flex items-center gap-1">
                  {col.header}
                  {col.sortable && (
                    <SortIndicator
                      active={sortKey === col.key}
                      direction={sortKey === col.key ? sortDir : null}
                    />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-nova-border bg-nova-bg">
          {loading ? (
            Array.from({ length: skeletonRows }).map((_, ri) => (
              <tr key={`skel-${ri}`}>
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3">
                    <SkeletonLine className="h-4 w-full" />
                  </td>
                ))}
              </tr>
            ))
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-12 text-center text-sm text-nova-text-muted"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr
                key={keyExtractor(row)}
                className="transition-colors hover:bg-nova-surface-hover"
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cn('px-4 py-3 text-sm text-nova-text', col.className)}
                  >
                    {col.render(row, index)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function SortIndicator({
  active,
  direction,
}: {
  active: boolean;
  direction: SortDir;
}) {
  if (!active || !direction) {
    return <ChevronUpDownIcon className="h-3.5 w-3.5 text-nova-text-muted" />;
  }
  return direction === 'asc' ? (
    <ChevronUpIcon className="h-3.5 w-3.5 text-primary-600" />
  ) : (
    <ChevronDownIcon className="h-3.5 w-3.5 text-primary-600" />
  );
}

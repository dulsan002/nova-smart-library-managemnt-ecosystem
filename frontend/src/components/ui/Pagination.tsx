/**
 * Pagination — cursor-based relay pagination controls.
 */

import {
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/20/solid';
import { cn } from '@/lib/utils';
import { Button } from './Button';

interface PageInfo {
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor?: string | null;
  endCursor?: string | null;
}

export interface PaginationProps {
  pageInfo: PageInfo;
  totalCount?: number;
  currentCount?: number;
  onNext: () => void;
  onPrev?: () => void;
  className?: string;
}

export function Pagination({
  pageInfo,
  totalCount,
  currentCount,
  onNext,
  onPrev,
  className,
}: PaginationProps) {
  const showInfo = totalCount !== undefined && currentCount !== undefined;

  return (
    <div
      className={cn(
        'flex items-center justify-between border-t border-nova-border pt-4',
        className,
      )}
    >
      <div className="text-sm text-nova-text-secondary">
        {showInfo && (
          <>
            Showing <span className="font-medium text-nova-text">{currentCount}</span>{' '}
            of <span className="font-medium text-nova-text">{totalCount}</span> results
          </>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={onPrev}
          disabled={!pageInfo.hasPreviousPage}
          leftIcon={<ChevronLeftIcon className="h-4 w-4" />}
        >
          Previous
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={onNext}
          disabled={!pageInfo.hasNextPage}
          rightIcon={<ChevronRightIcon className="h-4 w-4" />}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

/* ---------- Offset pagination (for simpler lists) ---------- */

interface OffsetPaginationProps {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
  className?: string;
}

export function OffsetPagination({
  page,
  totalPages,
  onChange,
  className,
}: OffsetPaginationProps) {
  const pages = getPageNumbers(page, totalPages);

  return (
    <nav
      className={cn(
        'flex items-center justify-center gap-1 border-t border-nova-border pt-4',
        className,
      )}
      aria-label="Pagination"
    >
      <button
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
        className="nova-focus rounded-lg p-2 text-nova-text-muted transition-colors hover:bg-nova-surface-hover disabled:cursor-not-allowed disabled:opacity-40"
      >
        <ChevronLeftIcon className="h-4 w-4" />
      </button>
      {pages.map((p, i) =>
        p === '...' ? (
          <span key={`ellipsis-${i}`} className="px-2 text-nova-text-muted">
            …
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p as number)}
            className={cn(
              'nova-focus min-w-[2rem] rounded-lg px-2.5 py-1.5 text-sm font-medium transition-colors',
              p === page
                ? 'bg-primary-600 text-white'
                : 'text-nova-text-secondary hover:bg-nova-surface-hover',
            )}
          >
            {p}
          </button>
        ),
      )}
      <button
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
        className="nova-focus rounded-lg p-2 text-nova-text-muted transition-colors hover:bg-nova-surface-hover disabled:cursor-not-allowed disabled:opacity-40"
      >
        <ChevronRightIcon className="h-4 w-4" />
      </button>
    </nav>
  );
}

function getPageNumbers(
  currentPage: number,
  totalPages: number,
): (number | '...')[] {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  const pages: (number | '...')[] = [1];

  if (currentPage > 3) pages.push('...');

  const start = Math.max(2, currentPage - 1);
  const end = Math.min(totalPages - 1, currentPage + 1);

  for (let i = start; i <= end; i++) pages.push(i);

  if (currentPage < totalPages - 2) pages.push('...');

  pages.push(totalPages);

  return pages;
}

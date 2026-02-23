/**
 * Spinner & LoadingScreen — loading indicators.
 */

import { cn } from '@/lib/utils';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const spinnerSizes = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-10 w-10',
};

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <svg
      className={cn('animate-spin text-primary-600', spinnerSizes[size], className)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      role="status"
      aria-label="Loading"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

export function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-nova-bg">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="h-14 w-14 rounded-full border-4 border-primary-200 dark:border-primary-800" />
          <div className="absolute inset-0 h-14 w-14 animate-spin rounded-full border-4 border-transparent border-t-primary-600" />
        </div>
        <p className="text-sm font-medium text-nova-text-secondary">Loading…</p>
      </div>
    </div>
  );
}

export function LoadingOverlay({ message }: { message?: string }) {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        {message && (
          <p className="text-sm text-nova-text-secondary">{message}</p>
        )}
      </div>
    </div>
  );
}

export function SkeletonLine({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'nova-shimmer h-4 rounded-md bg-gray-200 dark:bg-gray-700',
        className,
      )}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="nova-card space-y-3 p-5">
      <SkeletonLine className="h-5 w-2/3" />
      <SkeletonLine className="w-full" />
      <SkeletonLine className="w-4/5" />
      <SkeletonLine className="h-3 w-1/3" />
    </div>
  );
}

/**
 * EmptyState — placeholder when there is no data.
 */

import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-nova-border px-6 py-16 text-center',
        className,
      )}
    >
      {icon && (
        <div className="mb-4 text-nova-text-muted [&>svg]:h-12 [&>svg]:w-12">
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-nova-text">{title}</h3>
      {description && (
        <p className="mt-1.5 max-w-sm text-sm text-nova-text-secondary">
          {description}
        </p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

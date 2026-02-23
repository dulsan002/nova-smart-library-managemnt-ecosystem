/**
 * Card component — container with nova-card styling.
 */

import { forwardRef, type HTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
}

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-6',
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ padding = 'md', hoverable = false, className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'nova-card',
          paddingStyles[padding],
          hoverable &&
            'cursor-pointer transition-shadow hover:shadow-md hover:ring-1 hover:ring-primary-200 dark:hover:ring-primary-800',
          className,
        )}
        {...props}
      >
        {children}
      </div>
    );
  },
);

Card.displayName = 'Card';

/* ---------- Sub-components ---------- */

export function CardHeader({
  title,
  description,
  action,
  className,
  children,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
  className?: string;
  children?: ReactNode;
}) {
  // If children provided, render them directly (flexible mode)
  if (children) {
    return (
      <div className={cn('flex items-start justify-between gap-3 mb-3', className)}>
        {children}
      </div>
    );
  }

  return (
    <div className={cn('flex items-start justify-between mb-3', className)}>
      <div>
        {title && <h3 className="text-base font-semibold text-nova-text">{title}</h3>}
        {description && (
          <p className="mt-1 text-sm text-nova-text-secondary">{description}</p>
        )}
      </div>
      {action && <div className="ml-4 flex-shrink-0">{action}</div>}
    </div>
  );
}

export function CardFooter({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'mt-4 flex items-center justify-end gap-3 border-t border-nova-border pt-4',
        className,
      )}
    >
      {children}
    </div>
  );
}

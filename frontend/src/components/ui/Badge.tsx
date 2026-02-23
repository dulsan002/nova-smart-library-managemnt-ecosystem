/**
 * Badge component — status / category indicator.
 */

import { type HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

type BadgeVariant =
  | 'primary'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral'
  | 'kp-bronze'
  | 'kp-silver'
  | 'kp-gold'
  | 'kp-platinum'
  | 'kp-diamond';

type BadgeSize = 'xs' | 'sm' | 'md';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  primary: 'nova-badge-primary',
  success: 'nova-badge-success',
  warning: 'nova-badge-warning',
  danger: 'nova-badge-danger',
  info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  neutral:
    'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  'kp-bronze': 'nova-kp-bronze',
  'kp-silver': 'nova-kp-silver',
  'kp-gold': 'nova-kp-gold',
  'kp-platinum': 'nova-kp-platinum',
  'kp-diamond': 'nova-kp-diamond',
};

const sizeStyles: Record<BadgeSize, string> = {
  xs: 'px-1.5 py-0.5 text-[10px]',
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
};

const dotColors: Record<BadgeVariant, string> = {
  primary: 'bg-primary-500',
  success: 'bg-green-500',
  warning: 'bg-amber-500',
  danger: 'bg-red-500',
  info: 'bg-blue-500',
  neutral: 'bg-gray-500',
  'kp-bronze': 'bg-orange-700',
  'kp-silver': 'bg-gray-400',
  'kp-gold': 'bg-yellow-500',
  'kp-platinum': 'bg-cyan-500',
  'kp-diamond': 'bg-violet-500',
};

export function Badge({
  variant = 'neutral',
  size = 'sm',
  dot = false,
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full font-medium',
        variantStyles[variant],
        sizeStyles[size],
        className,
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn('h-1.5 w-1.5 rounded-full', dotColors[variant])}
        />
      )}
      {children}
    </span>
  );
}

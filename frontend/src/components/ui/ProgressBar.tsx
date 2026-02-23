/**
 * ProgressBar — progress indicator for reading, KP, etc.
 */

import { cn } from '@/lib/utils';

interface ProgressBarProps {
  value: number; // 0–100
  max?: number;
  label?: string;
  showValue?: boolean;
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'accent' | 'success' | 'warning' | 'danger';
  className?: string;
}

const sizes = {
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-4',
};

const colors = {
  primary: 'bg-primary-600',
  accent: 'bg-accent-600',
  success: 'bg-green-500',
  warning: 'bg-amber-500',
  danger: 'bg-red-500',
};

export function ProgressBar({
  value,
  max = 100,
  label,
  showValue = false,
  size = 'md',
  color = 'primary',
  className,
}: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn('w-full', className)}>
      {(label || showValue) && (
        <div className="mb-1.5 flex items-center justify-between text-sm">
          {label && (
            <span className="font-medium text-nova-text">{label}</span>
          )}
          {showValue && (
            <span className="text-nova-text-secondary">{Math.round(pct)}%</span>
          )}
        </div>
      )}
      <div
        className={cn(
          'w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700',
          sizes[size],
        )}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label || 'Progress'}
      >
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500 ease-out',
            colors[color],
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

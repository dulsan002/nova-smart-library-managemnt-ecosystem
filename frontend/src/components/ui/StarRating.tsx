/**
 * StarRating — interactive / display star rating for book reviews.
 */

import { useState } from 'react';
import { StarIcon } from '@heroicons/react/24/solid';
import { StarIcon as StarOutlineIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

interface StarRatingProps {
  value: number;
  onChange?: (value: number) => void;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  readonly?: boolean;
  showLabel?: boolean;
  className?: string;
}

const sizes = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
};

export function StarRating({
  value,
  onChange,
  max = 5,
  size = 'md',
  readonly = false,
  showLabel = false,
  className,
}: StarRatingProps) {
  const [hovered, setHovered] = useState(0);
  const interactive = !readonly && !!onChange;
  const numericValue = Number(value) || 0;
  const display = hovered || numericValue;

  return (
    <div
      className={cn('inline-flex items-center gap-0.5', className)}
      onMouseLeave={() => interactive && setHovered(0)}
    >
      {Array.from({ length: max }, (_, i) => {
        const starValue = i + 1;
        const filled = starValue <= display;

        return (
          <button
            key={starValue}
            type="button"
            disabled={!interactive}
            onClick={() => interactive && onChange?.(starValue)}
            onMouseEnter={() => interactive && setHovered(starValue)}
            className={cn(
              'transition-colors',
              interactive
                ? 'cursor-pointer hover:scale-110'
                : 'cursor-default',
              filled ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600',
            )}
            aria-label={`${starValue} star${starValue > 1 ? 's' : ''}`}
          >
            {filled ? (
              <StarIcon className={sizes[size]} />
            ) : (
              <StarOutlineIcon className={sizes[size]} />
            )}
          </button>
        );
      })}
      {showLabel && (
        <span className="ml-1.5 text-sm font-medium text-nova-text-secondary">
          {Number(numericValue).toFixed(1)}
        </span>
      )}
    </div>
  );
}

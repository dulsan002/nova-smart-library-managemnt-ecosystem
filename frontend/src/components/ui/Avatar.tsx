/**
 * Avatar component — user avatar with image or initials fallback.
 */

import { cn, getInitials } from '@/lib/utils';

type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface AvatarProps {
  src?: string | null;
  name: string;
  size?: AvatarSize;
  className?: string;
}

const sizeStyles: Record<AvatarSize, string> = {
  xs: 'h-6 w-6 text-[10px]',
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
  xl: 'h-16 w-16 text-lg',
};

const colorPalette = [
  'bg-primary-500',
  'bg-accent-500',
  'bg-emerald-500',
  'bg-amber-500',
  'bg-rose-500',
  'bg-cyan-500',
  'bg-violet-500',
  'bg-orange-500',
];

function getAvatarColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colorPalette[Math.abs(hash) % colorPalette.length] ?? 'bg-primary-500';
}

export function Avatar({ src, name, size = 'md', className }: AvatarProps) {
  const parts = name.split(' ');
  const initials = getInitials(parts[0], parts.length > 1 ? parts[parts.length - 1] : undefined);

  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={cn(
          'inline-flex shrink-0 items-center justify-center rounded-full object-cover ring-2 ring-white dark:ring-gray-800',
          sizeStyles[size],
          className,
        )}
        onError={(e) => {
          // Hide broken image and show fallback
          (e.target as HTMLImageElement).style.display = 'none';
          const parent = (e.target as HTMLImageElement).parentElement;
          if (parent) {
            const fallback = parent.querySelector('[data-avatar-fallback]');
            if (fallback) (fallback as HTMLElement).style.display = 'flex';
          }
        }}
      />
    );
  }

  return (
    <span
      data-avatar-fallback
      className={cn(
        'inline-flex shrink-0 items-center justify-center rounded-full font-semibold text-white ring-2 ring-white dark:ring-gray-800',
        sizeStyles[size],
        getAvatarColor(name),
        className,
      )}
      title={name}
    >
      {initials}
    </span>
  );
}

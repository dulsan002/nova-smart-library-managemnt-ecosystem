/**
 * Utility functions for the Nova frontend.
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { formatDistanceToNow, format, parseISO, isValid } from 'date-fns';

/** Merge Tailwind classes with conflict resolution */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Format a date string for display */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '—';
  const d = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(d)) return '—';
  return format(d, 'MMM d, yyyy');
}

/** Relative time (e.g., "3 hours ago") */
export function timeAgo(date: string | Date | null | undefined): string {
  if (!date) return '—';
  const d = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(d)) return '—';
  return formatDistanceToNow(d, { addSuffix: true });
}

/** Format date+time */
export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return '—';
  const d = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(d)) return '—';
  return format(d, 'MMM d, yyyy HH:mm');
}

/** Truncate text to max length */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 1) + '…';
}

/** Capitalize first letter */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/** Format a number with commas */
export function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n);
}

/** Format currency */
export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(amount);
}

/** Debounce a function */
export function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  ms: number,
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

/** Generate initials from a name */
export function getInitials(firstName?: string, lastName?: string): string {
  const f = firstName?.charAt(0)?.toUpperCase() ?? '';
  const l = lastName?.charAt(0)?.toUpperCase() ?? '';
  return f + l || '?';
}

/** Convert KP level to display name */
export function kpLevelName(level: number): string {
  const levels: Record<number, string> = {
    1: 'Bronze',
    2: 'Silver',
    3: 'Gold',
    4: 'Platinum',
    5: 'Diamond',
  };
  return levels[level] ?? `Level ${level}`;
}

/** KP level to badge CSS class */
export function kpLevelClass(level: number): string {
  const classes: Record<number, string> = {
    1: 'nova-kp-bronze',
    2: 'nova-kp-silver',
    3: 'nova-kp-gold',
    4: 'nova-kp-platinum',
    5: 'nova-kp-diamond',
  };
  return classes[level] ?? 'nova-badge-primary';
}

/** Risk level to color */
export function riskColor(risk: string): string {
  switch (risk) {
    case 'CRITICAL': return 'text-red-600 dark:text-red-400';
    case 'HIGH': return 'text-orange-600 dark:text-orange-400';
    case 'MODERATE': return 'text-amber-600 dark:text-amber-400';
    case 'LOW': return 'text-emerald-600 dark:text-emerald-400';
    default: return 'text-nova-text-secondary';
  }
}

/** Sleep for ms */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Extract GraphQL error message */
export function extractGqlError(error: unknown): string {
  if (!error) return 'An unexpected error occurred';
  if (typeof error === 'string') return error;
  const err = error as { graphQLErrors?: Array<{ message: string }>; message?: string };
  if (err.graphQLErrors?.length) return err.graphQLErrors[0]?.message ?? 'GraphQL error';
  if (err.message) return err.message;
  return 'An unexpected error occurred';
}

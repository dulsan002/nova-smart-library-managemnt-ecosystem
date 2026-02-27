/**
 * Application constants.
 */

export const APP_NAME = import.meta.env.VITE_APP_NAME || 'Nova Library';

export const ROLES = {
  SUPER_ADMIN: 'SUPER_ADMIN',
  LIBRARIAN: 'LIBRARIAN',
  ASSISTANT: 'ASSISTANT',
  USER: 'USER',
} as const;

export type UserRole = (typeof ROLES)[keyof typeof ROLES];

export const ADMIN_ROLES: UserRole[] = ['SUPER_ADMIN', 'LIBRARIAN', 'ASSISTANT'];
export const STAFF_ROLES: UserRole[] = ['SUPER_ADMIN', 'LIBRARIAN'];

export const BORROW_STATUS = {
  ACTIVE: 'ACTIVE',
  RETURNED: 'RETURNED',
  OVERDUE: 'OVERDUE',
  LOST: 'LOST',
} as const;

export const RESERVATION_STATUS = {
  PENDING: 'PENDING',
  READY: 'READY',
  FULFILLED: 'FULFILLED',
  CANCELLED: 'CANCELLED',
  EXPIRED: 'EXPIRED',
} as const;

export const FINE_STATUS = {
  PENDING: 'PENDING',
  PAID: 'PAID',
  WAIVED: 'WAIVED',
  OVERDUE: 'OVERDUE',
} as const;

export const NOTIFICATION_TYPES = {
  OVERDUE_WARNING: 'OVERDUE_WARNING',
  RECOMMENDATION: 'RECOMMENDATION',
  ACHIEVEMENT: 'ACHIEVEMENT',
  STREAK_REMINDER: 'STREAK_REMINDER',
  NEW_ARRIVAL: 'NEW_ARRIVAL',
  RESERVATION_READY: 'RESERVATION_READY',
  RE_ENGAGEMENT: 'RE_ENGAGEMENT',
  KP_MILESTONE: 'KP_MILESTONE',
  DUE_DATE_REMINDER: 'DUE_DATE_REMINDER',
} as const;

export const TRENDING_PERIODS = ['DAILY', 'WEEKLY', 'MONTHLY', 'ALL_TIME'] as const;

export const BOOK_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Spanish' },
  { code: 'fr', label: 'French' },
  { code: 'de', label: 'German' },
  { code: 'zh', label: 'Chinese' },
  { code: 'ja', label: 'Japanese' },
  { code: 'ko', label: 'Korean' },
  { code: 'pt', label: 'Portuguese' },
  { code: 'ar', label: 'Arabic' },
  { code: 'hi', label: 'Hindi' },
] as const;

export const ITEMS_PER_PAGE = 20;
export const MAX_SEARCH_SUGGESTIONS = 8;

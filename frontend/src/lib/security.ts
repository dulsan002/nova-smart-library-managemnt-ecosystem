/**
 * Security utilities for the Nova frontend.
 *
 * 1. **sanitizeHtml** – DOMPurify wrapper for safely rendering user-generated HTML.
 * 2. **useAutoLogout** – Hook that logs the user out after N minutes of inactivity.
 * 3. **SafeHtml** – React component that renders sanitized HTML.
 * 4. **csrfToken** – Reads the CSRF cookie (used for any non-GraphQL requests).
 */

import DOMPurify from 'dompurify';

// =============================================================================
// 1. HTML Sanitisation
// =============================================================================

/**
 * DOMPurify configuration – allow only safe tags/attributes.
 */
const PURIFY_CONFIG = {
  ALLOWED_TAGS: [
    'b', 'i', 'em', 'strong', 'u', 's', 'p', 'br', 'hr',
    'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'a', 'blockquote', 'code', 'pre', 'span', 'div',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'sup', 'sub', 'mark', 'abbr',
  ],
  ALLOWED_ATTR: [
    'href', 'title', 'class', 'id', 'target', 'rel',
    'colspan', 'rowspan', 'lang',
  ],
  ALLOW_DATA_ATTR: false,
  // Force all links to open in a new tab with noopener
  ADD_ATTR: ['target'],
} as const;

/**
 * Sanitise an HTML string, stripping dangerous tags/attributes.
 *
 * @param dirty – raw HTML from user input or API response
 * @returns safe HTML string
 */
export function sanitizeHtml(dirty: string): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const clean = String(DOMPurify.sanitize(dirty, PURIFY_CONFIG as any));

  // Ensure all <a> tags have rel="noopener noreferrer" and target="_blank"
  return clean
    .replace(/<a /g, '<a rel="noopener noreferrer" target="_blank" ');
}

/**
 * Strip ALL HTML tags, returning plain text.
 */
export function stripHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, { ALLOWED_TAGS: [] });
}

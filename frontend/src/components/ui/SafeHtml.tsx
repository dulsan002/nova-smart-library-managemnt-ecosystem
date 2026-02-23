/**
 * SafeHtml — Renders user-generated HTML safely via DOMPurify.
 *
 * Usage:
 *   <SafeHtml html={book.description} className="prose dark:prose-invert" />
 */

import { sanitizeHtml } from '@/lib/security';

interface SafeHtmlProps {
  html: string;
  className?: string;
  as?: keyof JSX.IntrinsicElements;
}

export default function SafeHtml({
  html,
  className = '',
  as: Tag = 'div',
}: SafeHtmlProps) {
  return (
    <Tag
      className={className}
      dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }}
    />
  );
}

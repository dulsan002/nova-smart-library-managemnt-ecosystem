/**
 * Textarea component — multi-line input with label, error, and helper text.
 */

import { forwardRef, type TextareaHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  wrapperClassName?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    { label, error, helperText, wrapperClassName, className, id, ...props },
    ref,
  ) => {
    const inputId = id || props.name;

    return (
      <div className={cn('space-y-1.5', wrapperClassName)}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-nova-text"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={cn(
            'nova-input w-full min-h-[80px] resize-y',
            error &&
              'border-red-500 focus:border-red-500 focus:ring-red-500/20 dark:border-red-400',
            className,
          )}
          aria-invalid={!!error}
          aria-describedby={
            error
              ? `${inputId}-error`
              : helperText
                ? `${inputId}-helper`
                : undefined
          }
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-sm text-red-500" role="alert">
            {error}
          </p>
        )}
        {!error && helperText && (
          <p id={`${inputId}-helper`} className="text-sm text-nova-text-muted">
            {helperText}
          </p>
        )}
      </div>
    );
  },
);

Textarea.displayName = 'Textarea';

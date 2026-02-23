/**
 * Input component — text input with label, error, and helper text.
 */

import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  wrapperClassName?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      wrapperClassName,
      className,
      id,
      ...props
    },
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
        <div className="relative">
          {leftIcon && (
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-nova-text-muted">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'nova-input w-full',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
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
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 text-nova-text-muted">
              {rightIcon}
            </div>
          )}
        </div>
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

Input.displayName = 'Input';

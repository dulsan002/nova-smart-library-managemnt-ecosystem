/**
 * SearchInput — search field with auto-suggest dropdown.
 */

import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/20/solid';
import { cn } from '@/lib/utils';

interface Suggestion {
  id: string;
  text: string;
  category?: string;
}

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: (value: string) => void;
  suggestions?: Suggestion[];
  onSuggestionClick?: (suggestion: Suggestion) => void;
  placeholder?: string;
  loading?: boolean;
  showSuggestions?: boolean;
  autoFocus?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeStyles = {
  sm: 'h-9 text-sm pl-9 pr-8',
  md: 'h-11 text-sm pl-11 pr-10',
  lg: 'h-14 text-base pl-12 pr-11',
};

const iconSizes = {
  sm: 'h-4 w-4 left-2.5',
  md: 'h-5 w-5 left-3',
  lg: 'h-5 w-5 left-3.5',
};

export function SearchInput({
  value,
  onChange,
  onSubmit,
  suggestions = [],
  onSuggestionClick,
  placeholder = 'Search…',
  loading = false,
  showSuggestions = false,
  autoFocus = false,
  className,
  size = 'md',
}: SearchInputProps) {
  const [activeIndex, setActiveIndex] = useState(-1);
  const listRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    setActiveIndex(-1);
  }, [suggestions]);

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter') {
        e.preventDefault();
        onSubmit?.(value);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : 0,
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex((prev) =>
          prev > 0 ? prev - 1 : suggestions.length - 1,
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (activeIndex >= 0 && suggestions[activeIndex]) {
          onSuggestionClick?.(suggestions[activeIndex]);
        } else {
          onSubmit?.(value);
        }
        break;
      case 'Escape':
        (e.target as HTMLInputElement).blur();
        break;
    }
  }

  return (
    <div className={cn('relative', className)}>
      {/* Icon */}
      <MagnifyingGlassIcon
        className={cn(
          'pointer-events-none absolute top-1/2 -translate-y-1/2 text-nova-text-muted',
          iconSizes[size],
        )}
      />

      {/* Input */}
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        autoFocus={autoFocus}
        autoComplete="off"
        className={cn(
          'nova-focus w-full rounded-xl border border-nova-border bg-nova-surface text-nova-text placeholder:text-nova-text-muted',
          sizeStyles[size],
        )}
        role="combobox"
        aria-expanded={showSuggestions && suggestions.length > 0}
        aria-controls="search-suggestions"
        aria-activedescendant={
          activeIndex >= 0 ? `suggestion-${activeIndex}` : undefined
        }
      />

      {/* Clear */}
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-md p-1 text-nova-text-muted transition-colors hover:text-nova-text"
        >
          <XMarkIcon className="h-4 w-4" />
        </button>
      )}

      {/* Loading indicator */}
      {loading && (
        <div className="absolute right-10 top-1/2 -translate-y-1/2">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-200 border-t-primary-600" />
        </div>
      )}

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <ul
          ref={listRef}
          id="search-suggestions"
          role="listbox"
          className="absolute z-50 mt-1 w-full overflow-auto rounded-xl border border-nova-border bg-nova-surface py-1 shadow-lg"
        >
          {suggestions.map((suggestion, idx) => (
            <li
              key={suggestion.id}
              id={`suggestion-${idx}`}
              role="option"
              aria-selected={idx === activeIndex}
              className={cn(
                'flex cursor-pointer items-center justify-between px-4 py-2.5 text-sm',
                idx === activeIndex
                  ? 'bg-primary-50 text-primary-900 dark:bg-primary-900/20 dark:text-primary-100'
                  : 'text-nova-text hover:bg-nova-surface-hover',
              )}
              onMouseEnter={() => setActiveIndex(idx)}
              onClick={() => onSuggestionClick?.(suggestion)}
            >
              <span className="flex items-center gap-2">
                <MagnifyingGlassIcon className="h-3.5 w-3.5 text-nova-text-muted" />
                {suggestion.text}
              </span>
              {suggestion.category && (
                <span className="text-xs text-nova-text-muted">
                  {suggestion.category}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

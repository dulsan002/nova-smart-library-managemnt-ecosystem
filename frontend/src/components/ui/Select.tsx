/**
 * Select component — custom dropdown using Headless UI Listbox.
 */

import { Fragment, type ReactNode } from 'react';
import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
  Transition,
} from '@headlessui/react';
import { CheckIcon, ChevronUpDownIcon } from '@heroicons/react/20/solid';
import { cn } from '@/lib/utils';

export interface SelectOption {
  value: string;
  label: string;
  description?: string;
  icon?: ReactNode;
  disabled?: boolean;
}

interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  label?: string;
  error?: string;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  wrapperClassName?: string;
}

export function Select({
  value,
  onChange,
  options,
  label,
  error,
  placeholder = 'Select an option',
  disabled = false,
  className,
  wrapperClassName,
}: SelectProps) {
  const selected = options.find((o) => o.value === value);

  return (
    <div className={cn('space-y-1.5', wrapperClassName)}>
      {label && (
        <span className="block text-sm font-medium text-nova-text">{label}</span>
      )}
      <Listbox value={value} onChange={onChange} disabled={disabled}>
        <div className="relative">
          <ListboxButton
            className={cn(
              'nova-input flex w-full items-center justify-between text-left',
              error &&
                'border-red-500 focus:border-red-500 focus:ring-red-500/20 dark:border-red-400',
              disabled && 'cursor-not-allowed opacity-50',
              className,
            )}
          >
            <span
              className={cn('block truncate', !selected && 'text-nova-text-muted')}
            >
              {selected ? (
                <span className="flex items-center gap-2">
                  {selected.icon}
                  {selected.label}
                </span>
              ) : (
                placeholder
              )}
            </span>
            <ChevronUpDownIcon className="h-5 w-5 text-nova-text-muted" />
          </ListboxButton>

          <Transition
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <ListboxOptions className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg bg-nova-surface py-1 shadow-lg ring-1 ring-nova-border focus:outline-none">
              {options.map((option) => (
                <ListboxOption
                  key={option.value}
                  value={option.value}
                  disabled={option.disabled}
                  className={({ active, selected: isSelected }) =>
                    cn(
                      'relative cursor-pointer select-none py-2 pl-10 pr-4 text-sm',
                      active && 'bg-primary-50 text-primary-900 dark:bg-primary-900/20 dark:text-primary-100',
                      isSelected && 'font-semibold',
                      !active && !isSelected && 'text-nova-text',
                      option.disabled && 'cursor-not-allowed opacity-40',
                    )
                  }
                >
                  {({ selected: isSelected }) => (
                    <>
                      <span className="flex items-center gap-2 truncate">
                        {option.icon}
                        {option.label}
                      </span>
                      {option.description && (
                        <span className="mt-0.5 block text-xs text-nova-text-muted">
                          {option.description}
                        </span>
                      )}
                      {isSelected && (
                        <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-primary-600">
                          <CheckIcon className="h-4 w-4" />
                        </span>
                      )}
                    </>
                  )}
                </ListboxOption>
              ))}
            </ListboxOptions>
          </Transition>
        </div>
      </Listbox>
      {error && (
        <p className="text-sm text-red-500" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

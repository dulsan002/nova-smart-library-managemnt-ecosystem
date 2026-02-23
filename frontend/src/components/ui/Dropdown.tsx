/**
 * Dropdown — menu dropdown using Headless UI Menu.
 */

import { Fragment, type ReactNode } from 'react';
import {
  Menu,
  MenuButton,
  MenuItem,
  MenuItems,
  Transition,
} from '@headlessui/react';
import { cn } from '@/lib/utils';

export interface DropdownItem {
  label: string;
  icon?: ReactNode;
  onClick: () => void;
  danger?: boolean;
  disabled?: boolean;
}

interface DropdownProps {
  trigger: ReactNode;
  items: DropdownItem[];
  align?: 'left' | 'right';
  className?: string;
}

export function Dropdown({
  trigger,
  items,
  align = 'right',
  className,
}: DropdownProps) {
  return (
    <Menu as="div" className={cn('relative inline-block text-left', className)}>
      <MenuButton as={Fragment}>{trigger}</MenuButton>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="opacity-0 scale-95"
        enterTo="opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="opacity-100 scale-100"
        leaveTo="opacity-0 scale-95"
      >
        <MenuItems
          className={cn(
            'absolute z-50 mt-2 w-56 origin-top-right rounded-xl border border-nova-border bg-nova-surface py-1 shadow-lg focus:outline-none',
            align === 'right' ? 'right-0' : 'left-0',
          )}
        >
          {items.map((item, idx) => (
            <MenuItem key={idx} disabled={item.disabled}>
              {({ active }) => (
                <button
                  onClick={item.onClick}
                  disabled={item.disabled}
                  className={cn(
                    'flex w-full items-center gap-2.5 px-4 py-2.5 text-sm transition-colors',
                    active && 'bg-nova-surface-hover',
                    item.danger
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-nova-text',
                    item.disabled && 'cursor-not-allowed opacity-40',
                  )}
                >
                  {item.icon && (
                    <span className="h-4 w-4 flex-shrink-0">{item.icon}</span>
                  )}
                  {item.label}
                </button>
              )}
            </MenuItem>
          ))}
        </MenuItems>
      </Transition>
    </Menu>
  );
}

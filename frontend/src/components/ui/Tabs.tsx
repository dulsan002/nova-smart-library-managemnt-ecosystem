/**
 * Tabs — tab navigation component using Headless UI Tab.
 */

import { type ReactNode } from 'react';
import {
  Tab,
  TabGroup,
  TabList,
  TabPanel,
  TabPanels,
} from '@headlessui/react';
import { cn } from '@/lib/utils';

export interface TabItem {
  label: string;
  icon?: ReactNode;
  badge?: string | number;
  content: ReactNode;
}

export interface TabsProps {
  tabs: TabItem[];
  defaultIndex?: number;
  /** Controlled active tab index. When provided, Tabs is controlled. */
  active?: number;
  onChange?: (index: number) => void;
  variant?: 'underline' | 'pills';
  className?: string;
}

export function Tabs({
  tabs,
  defaultIndex = 0,
  active,
  onChange,
  variant = 'underline',
  className,
}: TabsProps) {
  // Build controlled vs uncontrolled props
  const groupProps =
    active !== undefined
      ? { selectedIndex: active, onChange, className }
      : { defaultIndex, onChange, className };

  return (
    <TabGroup {...groupProps}>
      <TabList
        className={cn(
          'flex',
          variant === 'underline'
            ? 'border-b border-nova-border gap-0'
            : 'gap-1 rounded-xl bg-nova-surface p-1',
        )}
      >
        {tabs.map((tab, idx) => (
          <Tab
            key={idx}
            className={({ selected }) =>
              cn(
                'nova-focus inline-flex items-center gap-2 text-sm font-medium outline-none transition-colors',
                variant === 'underline'
                  ? cn(
                      'border-b-2 px-4 py-2.5',
                      selected
                        ? 'border-primary-600 text-primary-600'
                        : 'border-transparent text-nova-text-secondary hover:border-gray-300 hover:text-nova-text',
                    )
                  : cn(
                      'rounded-lg px-3.5 py-2',
                      selected
                        ? 'bg-white text-nova-text shadow-sm dark:bg-gray-700'
                        : 'text-nova-text-secondary hover:text-nova-text',
                    ),
              )
            }
          >
            {tab.icon}
            {tab.label}
            {tab.badge !== undefined && (
              <span
                className={cn(
                  'ml-1 inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold',
                  'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
                )}
              >
                {tab.badge}
              </span>
            )}
          </Tab>
        ))}
      </TabList>
      <TabPanels className="mt-4">
        {tabs.map((tab, idx) => (
          <TabPanel key={idx} className="nova-focus outline-none">
            {tab.content}
          </TabPanel>
        ))}
      </TabPanels>
    </TabGroup>
  );
}

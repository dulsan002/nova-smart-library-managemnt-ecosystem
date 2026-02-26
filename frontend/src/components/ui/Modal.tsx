/**
 * Modal component — dialog overlay using Headless UI Dialog + framer-motion.
 */

import { Fragment, type ReactNode } from 'react';
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  Transition,
  TransitionChild,
} from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: ReactNode;
  size?: ModalSize;
  showClose?: boolean;
  className?: string;
}

const sizeStyles: Record<ModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-xl',
  xl: 'max-w-3xl',
  '2xl': 'max-w-4xl',
  full: 'max-w-5xl',
};

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  size = 'md',
  showClose = true,
  className,
}: ModalProps) {
  return (
    <Transition show={open} as={Fragment}>
      <Dialog onClose={onClose} className="relative z-50">
        {/* Backdrop */}
        <TransitionChild
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" />
        </TransitionChild>

        {/* Panel */}
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <TransitionChild
            as={Fragment}
            enter="ease-out duration-200"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-150"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <DialogPanel
              className={cn(
                'flex w-full max-h-[90vh] flex-col rounded-2xl bg-nova-surface p-6 shadow-xl ring-1 ring-nova-border',
                sizeStyles[size],
                className,
              )}
            >
              {/* Header */}
              {(title || showClose) && (
                <div className="mb-4 flex items-start justify-between">
                  <div>
                    {title && (
                      <DialogTitle className="text-lg font-semibold text-nova-text">
                        {title}
                      </DialogTitle>
                    )}
                    {description && (
                      <p className="mt-1 text-sm text-nova-text-secondary">
                        {description}
                      </p>
                    )}
                  </div>
                  {showClose && (
                    <button
                      onClick={onClose}
                      className="nova-focus -mr-1 -mt-1 rounded-lg p-1.5 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text"
                    >
                      <XMarkIcon className="h-5 w-5" />
                      <span className="sr-only">Close</span>
                    </button>
                  )}
                </div>
              )}

              {/* Body — scrollable */}
              <div className="flex-1 min-h-0 overflow-y-auto nova-scrollbar">
                {children}
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </Dialog>
    </Transition>
  );
}

/* ---------- Convenience sub-components ---------- */

export function ModalBody({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cn('space-y-4', className)}>{children}</div>;
}

export function ModalFooter({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'mt-6 flex shrink-0 items-center justify-end gap-3 border-t border-nova-border pt-4',
        className,
      )}
    >
      {children}
    </div>
  );
}

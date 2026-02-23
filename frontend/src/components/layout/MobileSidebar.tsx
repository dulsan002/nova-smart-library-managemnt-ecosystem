/**
 * MobileSidebar — slide-out sidebar for mobile viewports.
 */

import { Fragment } from 'react';
import {
  Dialog,
  DialogPanel,
  Transition,
  TransitionChild,
} from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useUIStore } from '@/stores/uiStore';
import { Sidebar } from './Sidebar';

export function MobileSidebar() {
  const { sidebarOpen, setSidebarOpen } = useUIStore();

  return (
    <Transition show={sidebarOpen} as={Fragment}>
      <Dialog onClose={() => setSidebarOpen(false)} className="relative z-40 lg:hidden">
        <TransitionChild
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/30 backdrop-blur-sm" />
        </TransitionChild>

        <TransitionChild
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="-translate-x-full"
          enterTo="translate-x-0"
          leave="ease-in duration-150"
          leaveFrom="translate-x-0"
          leaveTo="-translate-x-full"
        >
          <DialogPanel className="fixed inset-y-0 left-0 z-50 flex">
            <Sidebar />
            <button
              onClick={() => setSidebarOpen(false)}
              className="nova-focus ml-2 mt-3 rounded-full bg-nova-surface p-2 text-nova-text-muted shadow-lg"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </DialogPanel>
        </TransitionChild>
      </Dialog>
    </Transition>
  );
}

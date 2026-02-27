/**
 * AppLayout — main authenticated layout with sidebar, header, and content area.
 */

import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Breadcrumbs } from './Breadcrumbs';
import { MobileSidebar } from './MobileSidebar';
import { LoadingScreen } from '@/components/ui/Spinner';

export function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-nova-bg">
      {/* Desktop sidebar */}
      <div className="hidden lg:flex">
        <Sidebar />
      </div>

      {/* Mobile sidebar */}
      <MobileSidebar />

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto nova-scrollbar">
          <div className="mx-auto w-full px-4 py-6 sm:px-6 lg:px-8 2xl:px-12">
            <Breadcrumbs className="mb-4" />
            <Suspense fallback={<LoadingScreen />}>
              <Outlet />
            </Suspense>
          </div>
        </main>
      </div>
    </div>
  );
}

/**
 * NotFoundPage — 404 fallback with navigation back to dashboard.
 */

import { Link } from 'react-router-dom';
import { HomeIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { Button } from '@/components/ui/Button';

export default function NotFoundPage() {
  useDocumentTitle('Page Not Found');

  return (
    <div className="flex min-h-screen items-center justify-center bg-nova-bg px-4">
      <div className="max-w-md text-center animate-fade-in">
        {/* Large 404 */}
        <div className="relative">
          <p className="text-[120px] font-black leading-none text-primary-100 dark:text-primary-900/30 select-none">
            404
          </p>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="rounded-full bg-primary-50 p-4 dark:bg-primary-900/20">
              <svg
                className="h-12 w-12 text-primary-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"
                />
              </svg>
            </div>
          </div>
        </div>

        <h1 className="mt-2 text-2xl font-bold text-nova-text">Page not found</h1>
        <p className="mt-2 text-nova-text-secondary">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="mt-8 flex items-center justify-center gap-3">
          <Button
            variant="outline"
            leftIcon={<ArrowLeftIcon className="h-4 w-4" />}
            onClick={() => window.history.back()}
          >
            Go Back
          </Button>
          <Link to="/dashboard">
            <Button leftIcon={<HomeIcon className="h-4 w-4" />}>Dashboard</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

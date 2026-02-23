/**
 * AuthLayout — split-screen layout for login / register pages.
 */

import { Suspense } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { ADMIN_ROLES } from '@/lib/constants';
import { LoadingScreen } from '@/components/ui/Spinner';

export function AuthLayout() {
  const token = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);

  // Redirect to respective panel if already authenticated
  if (token) {
    const dest =
      user && ADMIN_ROLES.includes(user.role)
        ? '/admin/dashboard'
        : '/dashboard';
    return <Navigate to={dest} replace />;
  }

  return (
    <div className="flex min-h-screen bg-nova-bg">
      {/* Left: Feature panel */}
      <div className="hidden w-1/2 flex-col justify-between bg-gradient-to-br from-primary-600 via-primary-700 to-accent-700 px-12 py-12 text-white lg:flex">
        <div>
          <h1 className="text-3xl font-bold">
            Nova<span className="text-primary-200">Lib</span>
          </h1>
          <p className="mt-2 text-primary-200">
            Intelligent Digital Library & Knowledge Engagement Ecosystem
          </p>
        </div>

        <div className="space-y-8">
          <FeatureItem
            title="AI-Powered Recommendations"
            description="Personalized book suggestions powered by collaborative filtering and content analysis."
          />
          <FeatureItem
            title="Knowledge Points & Gamification"
            description="Earn KP through reading, reviews, and achievements. Climb the leaderboard."
          />
          <FeatureItem
            title="Smart Reading Analytics"
            description="Track your reading pace, patterns, and engagement with interactive insights."
          />
        </div>

        <p className="text-sm text-primary-300">
          &copy; {new Date().getFullYear()} Nova Library Ecosystem
        </p>
      </div>

      {/* Right: Auth form */}
      <div className="flex w-full items-center justify-center px-6 py-12 lg:w-1/2">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="mb-8 lg:hidden">
            <h1 className="text-2xl font-bold text-primary-600">
              Nova<span className="text-accent-500">Lib</span>
            </h1>
          </div>
          <Suspense fallback={<LoadingScreen />}>
            <Outlet />
          </Suspense>
        </div>
      </div>
    </div>
  );
}

function FeatureItem({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-primary-200">{description}</p>
    </div>
  );
}

/**
 * AuthLayout — polished split-screen layout for login / register pages.
 */

import { Suspense } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { ADMIN_ROLES } from '@/lib/constants';
import { LoadingScreen } from '@/components/ui/Spinner';
import {
  SparklesIcon,
  TrophyIcon,
  ChartBarIcon,
  BookOpenIcon,
} from '@heroicons/react/24/outline';

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
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-accent-700 px-12 py-12 text-white lg:flex">
        {/* Decorative background elements */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -left-20 -top-20 h-72 w-72 rounded-full bg-white/5 blur-3xl" />
          <div className="absolute -bottom-32 -right-20 h-96 w-96 rounded-full bg-accent-500/10 blur-3xl" />
          <div className="absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary-400/10 blur-3xl" />
          {/* Grid pattern overlay */}
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage:
                'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)',
              backgroundSize: '40px 40px',
            }}
          />
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 backdrop-blur-sm">
              <BookOpenIcon className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                Nova<span className="text-primary-200">Lib</span>
              </h1>
            </div>
          </div>
          <p className="mt-3 max-w-sm text-sm text-primary-200/90">
            Intelligent Digital Library & Knowledge Engagement Ecosystem
          </p>
        </div>

        <div className="relative z-10 space-y-6">
          <FeatureItem
            icon={<SparklesIcon className="h-5 w-5" />}
            title="AI-Powered Recommendations"
            description="Personalized book suggestions powered by collaborative filtering and content analysis."
          />
          <FeatureItem
            icon={<TrophyIcon className="h-5 w-5" />}
            title="Knowledge Points & Gamification"
            description="Earn KP through reading, reviews, and achievements. Climb the leaderboard."
          />
          <FeatureItem
            icon={<ChartBarIcon className="h-5 w-5" />}
            title="Smart Reading Analytics"
            description="Track your reading pace, patterns, and engagement with interactive insights."
          />
        </div>

        {/* Stats bar */}
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-6 rounded-2xl bg-white/10 px-6 py-4 backdrop-blur-sm">
            <StatItem value="10K+" label="Books" />
            <div className="h-8 w-px bg-white/20" />
            <StatItem value="5K+" label="Members" />
            <div className="h-8 w-px bg-white/20" />
            <StatItem value="98%" label="Satisfaction" />
          </div>
          <p className="text-xs text-primary-300/80">
            &copy; {new Date().getFullYear()} Nova Library Ecosystem. All
            rights reserved.
          </p>
        </div>
      </div>

      {/* Right: Auth form */}
      <div className="flex w-full items-center justify-center px-6 py-12 lg:w-1/2">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600 text-white">
              <BookOpenIcon className="h-5 w-5" />
            </div>
            <h1 className="text-xl font-bold text-primary-600 dark:text-primary-400">
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
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/10 backdrop-blur-sm">
        {icon}
      </div>
      <div>
        <h3 className="text-sm font-semibold">{title}</h3>
        <p className="mt-0.5 text-xs leading-relaxed text-primary-200/80">
          {description}
        </p>
      </div>
    </div>
  );
}

function StatItem({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs text-primary-200/80">{label}</div>
    </div>
  );
}

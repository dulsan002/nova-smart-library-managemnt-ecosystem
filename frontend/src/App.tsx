import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';

import { AppLayout } from '@/components/layout/AppLayout';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminRoute } from '@/components/auth/AdminRoute';
import { LoadingScreen } from '@/components/ui/Spinner';

// --- Lazy-loaded pages ---
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'));
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const CatalogPage = lazy(() => import('@/pages/catalog/CatalogPage'));
const BookDetailPage = lazy(() => import('@/pages/catalog/BookDetailPage'));
const SearchPage = lazy(() => import('@/pages/SearchPage'));
const MyBorrowsPage = lazy(() => import('@/pages/circulation/MyBorrowsPage'));
const MyReservationsPage = lazy(() => import('@/pages/circulation/MyReservationsPage'));
const MyFinesPage = lazy(() => import('@/pages/circulation/MyFinesPage'));
const DigitalLibraryPage = lazy(() => import('@/pages/digital/DigitalLibraryPage'));
const ReaderPage = lazy(() => import('@/pages/digital/ReaderPage'));
const AudiobookPlayerPage = lazy(() => import('@/pages/digital/AudiobookPlayerPage'));
const ProfilePage = lazy(() => import('@/pages/ProfilePage'));
const AchievementsPage = lazy(() => import('@/pages/engagement/AchievementsPage'));
const LeaderboardPage = lazy(() => import('@/pages/engagement/LeaderboardPage'));
const KnowledgePointsPage = lazy(() => import('@/pages/engagement/KnowledgePointsPage'));
const RecommendationsPage = lazy(() => import('@/pages/intelligence/RecommendationsPage'));
const NotificationsPage = lazy(() => import('@/pages/intelligence/NotificationsPage'));
const ReadingInsightsPage = lazy(() => import('@/pages/intelligence/ReadingInsightsPage'));

// Admin pages
const AdminDashboardPage = lazy(() => import('@/pages/admin/AdminDashboardPage'));
const AdminUsersPage = lazy(() => import('@/pages/admin/AdminUsersPage'));
const AdminBooksPage = lazy(() => import('@/pages/admin/AdminBooksPage'));
const AdminCirculationPage = lazy(() => import('@/pages/admin/AdminCirculationPage'));
const AdminAnalyticsPage = lazy(() => import('@/pages/admin/AdminAnalyticsPage'));
const AdminAIModelsPage = lazy(() => import('@/pages/admin/AdminAIModelsPage'));
const AdminAIConfigPage = lazy(() => import('@/pages/admin/AdminAIConfigPage'));
const AdminAuditPage = lazy(() => import('@/pages/admin/AdminAuditPage'));
const AdminAssetsPage = lazy(() => import('@/pages/admin/AdminAssetsPage'));
const AdminEmployeesPage = lazy(() => import('@/pages/admin/AdminEmployeesPage'));
const AdminSettingsPage = lazy(() => import('@/pages/admin/AdminSettingsPage'));
const AdminDigitalPage = lazy(() => import('@/pages/admin/AdminDigitalPage'));
const AdminAuthorsPage = lazy(() => import('@/pages/admin/AdminAuthorsPage'));
const AdminRolesPage = lazy(() => import('@/pages/admin/AdminRolesPage'));
const AdminMembersPage = lazy(() => import('@/pages/admin/AdminMembersPage'));

const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

export function App() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        {/* Auth routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        {/* Protected member routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />

            {/* Catalog & search */}
            <Route path="/catalog" element={<CatalogPage />} />
            <Route path="/catalog/:bookId" element={<BookDetailPage />} />
            <Route path="/search" element={<SearchPage />} />

            {/* Circulation */}
            <Route path="/borrows" element={<MyBorrowsPage />} />
            <Route path="/reservations" element={<MyReservationsPage />} />
            <Route path="/fines" element={<MyFinesPage />} />

            {/* Digital */}
            <Route path="/library" element={<DigitalLibraryPage />} />
            <Route path="/reader/:assetId" element={<ReaderPage />} />
            <Route path="/listen/:assetId" element={<AudiobookPlayerPage />} />

            {/* Profile */}
            <Route path="/profile" element={<ProfilePage />} />

            {/* Engagement */}
            <Route path="/achievements" element={<AchievementsPage />} />
            <Route path="/leaderboard" element={<LeaderboardPage />} />
            <Route path="/kp-center" element={<KnowledgePointsPage />} />

            {/* Intelligence */}
            <Route path="/recommendations" element={<RecommendationsPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/insights" element={<ReadingInsightsPage />} />
          </Route>
        </Route>

        {/* Admin routes */}
        <Route element={<AdminRoute />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/books" element={<AdminBooksPage />} />
            <Route path="/admin/authors" element={<AdminAuthorsPage />} />
            <Route path="/admin/digital" element={<AdminDigitalPage />} />
            <Route path="/admin/circulation" element={<AdminCirculationPage />} />
            <Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
            <Route path="/admin/ai-models" element={<AdminAIModelsPage />} />
            <Route path="/admin/ai-config" element={<AdminAIConfigPage />} />
            <Route path="/admin/audit" element={<AdminAuditPage />} />
            <Route path="/admin/assets" element={<AdminAssetsPage />} />
            <Route path="/admin/employees" element={<AdminEmployeesPage />} />
            <Route path="/admin/jobs" element={<AdminEmployeesPage />} />
            <Route path="/admin/roles" element={<AdminRolesPage />} />
            <Route path="/admin/members" element={<AdminMembersPage />} />
            <Route path="/admin/settings" element={<AdminSettingsPage />} />
          </Route>
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}

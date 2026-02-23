/**
 * AchievementsPage — gamification achievements grid.
 */

import { useQuery } from '@apollo/client';
import {
  TrophyIcon,
  CheckBadgeIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { MY_ACHIEVEMENTS, ALL_ACHIEVEMENTS } from '@/graphql/queries/engagement';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatDate } from '@/lib/utils';

export default function AchievementsPage() {
  useDocumentTitle('Achievements');

  const { data: myData, loading: myLoading } = useQuery(MY_ACHIEVEMENTS);
  const { data: allData, loading: allLoading } = useQuery(ALL_ACHIEVEMENTS);

  const myAchievements = myData?.myAchievements ?? [];
  const allAchievements = allData?.allAchievements ?? [];

  const earnedIds = new Set(myAchievements.map((a: any) => a.achievement?.id ?? a.id));

  const loading = myLoading || allLoading;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-nova-text">Achievements</h1>
        <p className="text-sm text-nova-text-secondary">
          {myAchievements.length} of {allAchievements.length} earned
        </p>
      </div>

      {/* Summary */}
      <Card className="flex items-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-100 text-amber-600 dark:bg-amber-900/30">
          <TrophyIcon className="h-7 w-7" />
        </div>
        <div>
          <p className="text-2xl font-bold text-nova-text">{myAchievements.length}</p>
          <p className="text-sm text-nova-text-secondary">Achievements Earned</p>
        </div>
        <div className="ml-auto">
          <ProgressBar
            value={myAchievements.length}
            max={Math.max(allAchievements.length, 1)}
            showValue
            size="md"
            color="accent"
            className="w-32"
          />
        </div>
      </Card>

      {loading ? (
        <LoadingOverlay />
      ) : allAchievements.length === 0 ? (
        <EmptyState
          icon={<TrophyIcon />}
          title="No achievements configured"
          description="Achievements will be added by the library administrators."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {allAchievements.map((achievement: any) => {
            const earned = earnedIds.has(achievement.id);
            const earnedData = myAchievements.find(
              (a: any) => (a.achievement?.id ?? a.id) === achievement.id,
            );

            return (
              <Card
                key={achievement.id}
                className={earned ? '' : 'opacity-60'}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-xl text-2xl ${
                      earned
                        ? 'bg-amber-100 dark:bg-amber-900/30'
                        : 'bg-gray-100 dark:bg-gray-800'
                    }`}
                  >
                    {achievement.icon || (earned ? '🏆' : '🔒')}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-nova-text">
                        {achievement.name}
                      </h3>
                      {earned && (
                        <CheckBadgeIcon className="h-4 w-4 text-green-500" />
                      )}
                    </div>
                    <p className="mt-0.5 text-xs text-nova-text-secondary">
                      {achievement.description}
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <Badge
                        variant={earned ? 'success' : 'neutral'}
                        size="xs"
                      >
                        {earned ? 'Earned' : 'Locked'}
                      </Badge>
                      {achievement.kpReward && (
                        <Badge variant="kp-gold" size="xs">
                          +{achievement.kpReward} KP
                        </Badge>
                      )}
                    </div>
                    {earned && earnedData?.earnedAt && (
                      <p className="mt-1 text-[10px] text-nova-text-muted">
                        Earned {formatDate(earnedData.earnedAt)}
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

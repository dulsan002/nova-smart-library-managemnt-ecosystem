/**
 * LeaderboardPage — gamification leaderboard with ranks.
 */

import { useQuery } from '@apollo/client';
import {
  TrophyIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { LEADERBOARD, MY_RANK } from '@/graphql/queries/engagement';
import { Card } from '@/components/ui/Card';
import { Avatar } from '@/components/ui/Avatar';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { kpLevelName } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';

export default function LeaderboardPage() {
  useDocumentTitle('Leaderboard');

  const user = useAuthStore((s) => s.user);

  const { data: boardData, loading } = useQuery(LEADERBOARD, {
    variables: { limit: 50 },
  });

  const { data: rankData } = useQuery(MY_RANK);

  const leaderboard = boardData?.leaderboard ?? [];
  const myRank = rankData?.myRank;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-nova-text">Leaderboard</h1>
        <p className="text-sm text-nova-text-secondary">
          Knowledge Point rankings across the library
        </p>
      </div>

      {/* My rank card */}
      {myRank && (
        <Card className="bg-gradient-to-r from-primary-50 to-accent-50 dark:from-primary-900/10 dark:to-accent-900/10">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/80 text-2xl font-bold text-primary-600 shadow-sm dark:bg-gray-800/80">
              #{myRank.rank ?? '?'}
            </div>
            <div>
              <p className="text-sm text-nova-text-secondary">Your Rank</p>
              <p className="text-xl font-bold text-nova-text">
                {myRank.totalKp ?? 0} KP
              </p>
              <p className="text-xs text-nova-text-muted">
                Level {myRank.level ?? 1} — {kpLevelName(myRank.level ?? 1)}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Leaderboard table */}
      {loading ? (
        <LoadingOverlay />
      ) : leaderboard.length === 0 ? (
        <EmptyState
          icon={<TrophyIcon />}
          title="No rankings yet"
          description="Start earning Knowledge Points to appear on the leaderboard."
        />
      ) : (
        <Card padding="none">
          <div className="divide-y divide-nova-border">
            {leaderboard.map((entry: any, idx: number) => {
              const rank = entry.rank ?? idx + 1;
              const isMe = user?.id === entry.userId;

              return (
                <div
                  key={entry.userId ?? idx}
                  className={cn(
                    'flex items-center gap-4 px-5 py-3 transition-colors',
                    isMe && 'bg-primary-50/50 dark:bg-primary-900/10',
                  )}
                >
                  {/* Rank */}
                  <div className="w-10 text-center">
                    {rank <= 3 ? (
                      <span className="text-xl">
                        {rank === 1 ? '🥇' : rank === 2 ? '🥈' : '🥉'}
                      </span>
                    ) : (
                      <span className="text-sm font-bold text-nova-text-muted">
                        {rank}
                      </span>
                    )}
                  </div>

                  {/* User */}
                  <Avatar
                    name={entry.fullName ?? ''}
                    src={entry.avatarUrl}
                    size="sm"
                  />
                  <div className="min-w-0 flex-1">
                    <p className={cn('text-sm font-medium', isMe ? 'text-primary-600' : 'text-nova-text')}>
                      {entry.fullName}
                      {isMe && ' (You)'}
                    </p>
                    <p className="text-xs text-nova-text-muted">
                      Level {entry.level ?? 1} — {entry.levelTitle ?? kpLevelName(entry.level ?? 1)}
                    </p>
                  </div>

                  {/* KP */}
                  <div className="text-right">
                    <p className="text-sm font-bold text-nova-text">
                      {entry.totalKp ?? 0}
                    </p>
                    <p className="text-[10px] text-nova-text-muted">KP</p>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
}

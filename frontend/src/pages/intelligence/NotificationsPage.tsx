/**
 * NotificationsPage — user notification center with mark-read actions.
 */

import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  BellIcon,
  CheckIcon,
  CheckCircleIcon,
  BookOpenIcon,
  TrophyIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { MY_NOTIFICATIONS } from '@/graphql/queries/intelligence';
import {
  MARK_NOTIFICATION_READ,
  MARK_ALL_NOTIFICATIONS_READ,
} from '@/graphql/mutations/intelligence';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { timeAgo, extractGqlError, cn } from '@/lib/utils';

const typeIcons: Record<string, React.ReactNode> = {
  BORROW_DUE: <ExclamationTriangleIcon className="h-5 w-5 text-amber-500" />,
  BORROW_OVERDUE: <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />,
  RESERVATION_READY: <BookOpenIcon className="h-5 w-5 text-green-500" />,
  RECOMMENDATION: <SparklesIcon className="h-5 w-5 text-accent-500" />,
  ACHIEVEMENT: <TrophyIcon className="h-5 w-5 text-amber-500" />,
  KP_EARNED: <TrophyIcon className="h-5 w-5 text-primary-500" />,
  SYSTEM: <InformationCircleIcon className="h-5 w-5 text-blue-500" />,
};

export default function NotificationsPage() {
  useDocumentTitle('Notifications');

  const { data, loading, refetch } = useQuery(MY_NOTIFICATIONS, {
    fetchPolicy: 'cache-and-network',
  });

  const notifications = data?.myNotifications ?? [];
  const unread = notifications.filter((n: any) => !n.isRead);

  const [markRead] = useMutation(MARK_NOTIFICATION_READ, {
    onCompleted: () => refetch(),
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const [markAllRead, { loading: markingAll }] = useMutation(MARK_ALL_NOTIFICATIONS_READ, {
    onCompleted: () => {
      toast.success('All notifications marked as read');
      refetch();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">Notifications</h1>
          <p className="text-sm text-nova-text-secondary">
            {unread.length} unread notification{unread.length !== 1 ? 's' : ''}
          </p>
        </div>
        {unread.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            leftIcon={<CheckCircleIcon className="h-4 w-4" />}
            onClick={() => markAllRead()}
            isLoading={markingAll}
          >
            Mark all read
          </Button>
        )}
      </div>

      {loading ? (
        <LoadingOverlay />
      ) : notifications.length === 0 ? (
        <EmptyState
          icon={<BellIcon />}
          title="No notifications"
          description="You're all caught up! New notifications will appear here."
        />
      ) : (
        <div className="space-y-2">
          {notifications.map((notif: any) => (
            <Card
              key={notif.id}
              className={cn(
                'flex items-start gap-3 transition-colors',
                !notif.isRead && 'border-l-4 border-l-primary-500 bg-primary-50/30 dark:bg-primary-900/5',
              )}
            >
              <div className="mt-0.5 flex-shrink-0">
                {typeIcons[notif.notificationType] ?? typeIcons.SYSTEM}
              </div>
              <div className="min-w-0 flex-1">
                <p className={cn('text-sm', notif.isRead ? 'text-nova-text-secondary' : 'font-medium text-nova-text')}>
                  {notif.title ?? notif.message}
                </p>
                {notif.body && notif.body !== notif.title && (
                  <p className="mt-0.5 text-xs text-nova-text-muted">{notif.body}</p>
                )}
                <p className="mt-1 text-[10px] text-nova-text-muted">
                  {timeAgo(notif.createdAt)}
                </p>
              </div>
              {!notif.isRead && (
                <button
                  onClick={() => markRead({ variables: { notificationId: notif.id } })}
                  className="nova-focus flex-shrink-0 rounded-lg p-1.5 text-nova-text-muted transition-colors hover:bg-nova-surface-hover hover:text-nova-text"
                  title="Mark as read"
                >
                  <CheckIcon className="h-4 w-4" />
                </button>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

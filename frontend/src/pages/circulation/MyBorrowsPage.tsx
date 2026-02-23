/**
 * MyBorrowsPage — Unified view of reservations and borrows.
 *
 * Tabs:
 *   Reservations  – PENDING / READY reservations (with cancel)
 *   Active        – ACTIVE / OVERDUE borrows (with renew)
 *   History       – RETURNED / LOST borrows (read-only)
 *
 * Return is physical-only (handled by librarian), so no Return button.
 */

import { useQuery, useMutation } from '@apollo/client';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  BookOpenIcon,
  ArrowPathIcon,
  ClockIcon,
  MapPinIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { MY_BORROWS, MY_RESERVATIONS, MY_RESERVATION_BAN } from '@/graphql/queries/circulation';
import { RENEW_BORROW, CANCEL_RESERVATION } from '@/graphql/mutations/circulation';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { Tabs } from '@/components/ui/Tabs';
import { formatDate, extractGqlError } from '@/lib/utils';

export default function MyBorrowsPage() {
  useDocumentTitle('My Books');

  const { data: borrowsData, loading: borrowsLoading, refetch: refetchBorrows } = useQuery(MY_BORROWS, {
    variables: { limit: 50 },
    fetchPolicy: 'cache-and-network',
  });

  const { data: reservationsData, loading: reservationsLoading, refetch: refetchReservations } = useQuery(
    MY_RESERVATIONS,
    { fetchPolicy: 'cache-and-network' },
  );

  const { data: banData } = useQuery(MY_RESERVATION_BAN);

  const borrows = borrowsData?.myBorrows ?? [];
  const reservations = reservationsData?.myReservations ?? [];
  const ban = banData?.myReservationBan;

  const active = borrows.filter(
    (b: any) => b.status === 'ACTIVE' || b.status === 'OVERDUE',
  );
  const history = borrows.filter(
    (b: any) => b.status === 'RETURNED' || b.status === 'LOST',
  );

  const loading = borrowsLoading || reservationsLoading;

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold text-nova-text">My Books</h1>

      {/* Ban warning */}
      {ban?.isActive && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/30">
          <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0 text-red-500" />
          <div>
            <p className="font-semibold text-red-700 dark:text-red-400">Reservation Suspended</p>
            <p className="text-sm text-red-600 dark:text-red-400/80">{ban.reason}</p>
            <p className="text-xs text-red-500 mt-1">Expires: {formatDate(ban.expiresAt)}</p>
          </div>
        </div>
      )}

      {loading ? (
        <LoadingOverlay />
      ) : (
        <Tabs
          tabs={[
            {
              label: 'Reservations',
              badge: reservations.length,
              content: (
                <ReservationList
                  reservations={reservations}
                  onRefetch={refetchReservations}
                />
              ),
            },
            {
              label: 'Active',
              badge: active.length,
              content: (
                <BorrowList
                  borrows={active}
                  showRenew
                  onRefetch={refetchBorrows}
                  emptyTitle="No active borrows"
                  emptyDesc="Reserve a book from the catalog to get started."
                />
              ),
            },
            {
              label: 'History',
              badge: history.length,
              content: (
                <BorrowList
                  borrows={history}
                  onRefetch={refetchBorrows}
                  emptyTitle="No borrow history"
                  emptyDesc="Returned books will appear here."
                />
              ),
            },
          ]}
        />
      )}
    </div>
  );
}

/* ---------- ReservationList ---------- */

function ReservationList({
  reservations,
  onRefetch,
}: {
  reservations: any[];
  onRefetch: () => void;
}) {
  const [cancelReservation, { loading: cancelling }] = useMutation(CANCEL_RESERVATION, {
    onCompleted: () => {
      toast.success('Reservation cancelled.');
      onRefetch();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  if (reservations.length === 0) {
    return (
      <EmptyState
        icon={<ClockIcon />}
        title="No active reservations"
        description="Reserve a book from the catalog."
        action={
          <Link to="/catalog">
            <Button size="sm">Browse Catalog</Button>
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-3">
      {reservations.map((resv: any) => {
        const isReady = resv.status === 'READY';
        const hours = resv.hoursUntilExpiry ?? 0;

        return (
          <Card
            key={resv.id}
            className={`flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between ${
              isReady ? 'ring-2 ring-green-300 dark:ring-green-800' : ''
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="h-16 w-11 flex-shrink-0 overflow-hidden rounded-lg bg-gray-100 dark:bg-gray-800">
                {resv.book?.coverImageUrl ? (
                  <img src={resv.book.coverImageUrl} alt={resv.book.title} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <BookOpenIcon className="h-5 w-5 text-gray-300" />
                  </div>
                )}
              </div>
              <div className="min-w-0">
                <Link
                  to={`/catalog/${resv.book?.id}`}
                  className="truncate font-semibold text-nova-text hover:text-primary-600"
                >
                  {resv.book?.title ?? 'Unknown Book'}
                </Link>

                {isReady ? (
                  <div className="mt-1 space-y-0.5">
                    <p className="text-xs font-medium text-green-600 dark:text-green-400">
                      <MapPinIcon className="inline h-3.5 w-3.5 mr-0.5" />
                      Pickup: {resv.pickupLocation || 'Library Desk'}
                    </p>
                    <p className="text-xs text-green-600 dark:text-green-400">
                      <ClockIcon className="inline h-3.5 w-3.5 mr-0.5" />
                      {hours > 0
                        ? `${hours.toFixed(1)}h remaining`
                        : 'Deadline passed'}
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-nova-text-muted mt-1">
                    Queue position: #{resv.queuePosition} &middot; Reserved {formatDate(resv.reservedAt)}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Badge
                variant={isReady ? 'success' : 'primary'}
                size="sm"
                dot
              >
                {isReady ? 'Ready' : 'Pending'}
              </Badge>
              <Button
                variant="outline"
                size="xs"
                leftIcon={<XMarkIcon className="h-3.5 w-3.5" />}
                onClick={() => cancelReservation({ variables: { reservationId: resv.id } })}
                isLoading={cancelling}
              >
                Cancel
              </Button>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

/* ---------- BorrowList ---------- */

function BorrowList({
  borrows,
  showRenew = false,
  onRefetch,
  emptyTitle,
  emptyDesc,
}: {
  borrows: any[];
  showRenew?: boolean;
  onRefetch: () => void;
  emptyTitle: string;
  emptyDesc: string;
}) {
  const [renewBorrow, { loading: renewing }] = useMutation(RENEW_BORROW, {
    onCompleted: () => {
      toast.success('Borrow renewed successfully!');
      onRefetch();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  if (borrows.length === 0) {
    return (
      <EmptyState
        icon={<BookOpenIcon />}
        title={emptyTitle}
        description={emptyDesc}
        action={
          <Link to="/catalog">
            <Button size="sm">Browse Catalog</Button>
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-3">
      {borrows.map((borrow: any) => {
        const book = borrow.bookCopy?.book;
        const statusVariant =
          borrow.status === 'RETURNED'
            ? 'success'
            : borrow.status === 'OVERDUE'
              ? 'danger'
              : borrow.status === 'LOST'
                ? 'danger'
                : 'primary';

        return (
          <Card key={borrow.id} className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <div className="h-16 w-11 flex-shrink-0 overflow-hidden rounded-lg bg-gray-100 dark:bg-gray-800">
                {book?.coverImageUrl ? (
                  <img src={book.coverImageUrl} alt={book.title} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <BookOpenIcon className="h-5 w-5 text-gray-300" />
                  </div>
                )}
              </div>
              <div className="min-w-0">
                <Link to={`/catalog/${book?.id}`} className="truncate font-semibold text-nova-text hover:text-primary-600">
                  {book?.title ?? 'Unknown Book'}
                </Link>
                <p className="text-xs text-nova-text-muted">
                  Borrowed {formatDate(borrow.borrowedAt)} &middot; Due {formatDate(borrow.dueDate)}
                </p>
                {borrow.returnedAt && (
                  <p className="text-xs text-nova-text-muted">Returned {formatDate(borrow.returnedAt)}</p>
                )}
                {borrow.isOverdue && (
                  <p className="text-xs font-medium text-red-500">
                    Overdue by {borrow.daysOverdue} day{borrow.daysOverdue !== 1 ? 's' : ''}
                  </p>
                )}
                {showRenew && (
                  <p className="text-xs text-nova-text-muted">
                    Renewals: {borrow.renewalCount}/{borrow.maxRenewals}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Badge variant={statusVariant} size="sm" dot>
                {borrow.status}
              </Badge>
              {showRenew && borrow.canRenew && (
                <Button
                  variant="outline"
                  size="xs"
                  leftIcon={<ArrowPathIcon className="h-3.5 w-3.5" />}
                  onClick={() => renewBorrow({ variables: { borrowId: borrow.id } })}
                  isLoading={renewing}
                >
                  Renew
                </Button>
              )}
              {showRenew && !borrow.canRenew && borrow.status === 'ACTIVE' && (
                <span className="text-xs text-nova-text-muted italic">Max renewals reached</span>
              )}
            </div>
          </Card>
        );
      })}

      {/* Return info note */}
      {showRenew && borrows.length > 0 && (
        <p className="text-xs text-nova-text-muted text-center pt-2">
          To return a book, please visit the library physically. A librarian will process your return.
        </p>
      )}
    </div>
  );
}

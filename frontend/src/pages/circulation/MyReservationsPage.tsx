/**
 * MyReservationsPage — list of user's reservations with cancel action.
 */

import { useQuery, useMutation } from '@apollo/client';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { BookOpenIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { MY_RESERVATIONS } from '@/graphql/queries/circulation';
import { CANCEL_RESERVATION } from '@/graphql/mutations/circulation';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { formatDate, extractGqlError } from '@/lib/utils';
import { useState } from 'react';

export default function MyReservationsPage() {
  useDocumentTitle('Reservations');
  const [cancelId, setCancelId] = useState<string | null>(null);

  const { data, loading, refetch } = useQuery(MY_RESERVATIONS, {
    fetchPolicy: 'cache-and-network',
  });

  const reservations = (data?.myReservations ?? []).filter(Boolean);

  const [cancelReservation, { loading: cancelling }] = useMutation(CANCEL_RESERVATION, {
    onCompleted: () => {
      toast.success('Reservation cancelled');
      setCancelId(null);
      refetch();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold text-nova-text">My Reservations</h1>

      {loading ? (
        <LoadingOverlay />
      ) : reservations.length === 0 ? (
        <EmptyState
          icon={<BookOpenIcon />}
          title="No reservations"
          description="When all copies of a book are borrowed, you can reserve it here."
          action={
            <Link to="/catalog">
              <Button size="sm">Browse Catalog</Button>
            </Link>
          }
        />
      ) : (
        <div className="space-y-3">
          {reservations.map((res: any) => {
            const statusVariant =
              res.status === 'FULFILLED'
                ? 'success'
                : res.status === 'CANCELLED' || res.status === 'EXPIRED'
                  ? 'neutral'
                  : 'warning';

            return (
              <Card key={res.id} className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <Link
                    to={`/catalog/${res.book?.id}`}
                    className="font-semibold text-nova-text hover:text-primary-600"
                  >
                    {res.book?.title ?? 'Unknown Book'}
                  </Link>
                  <p className="text-xs text-nova-text-muted">
                    Reserved {formatDate(res.createdAt)}
                    {res.expiresAt && ` · Expires ${formatDate(res.expiresAt)}`}
                  </p>
                  {res.queuePosition && (
                    <p className="text-xs text-nova-text-muted">
                      Queue position: <span className="font-medium">{res.queuePosition}</span>
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={statusVariant} size="sm" dot>
                    {res.status}
                  </Badge>
                  {res.status === 'PENDING' && (
                    <Button
                      variant="ghost"
                      size="xs"
                      leftIcon={<XMarkIcon className="h-3.5 w-3.5" />}
                      onClick={() => setCancelId(res.id)}
                    >
                      Cancel
                    </Button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <ConfirmDialog
        open={!!cancelId}
        onClose={() => setCancelId(null)}
        onConfirm={() => cancelId && cancelReservation({ variables: { reservationId: cancelId } })}
        title="Cancel Reservation"
        message="Are you sure you want to cancel this reservation? You will lose your place in the queue."
        confirmLabel="Yes, Cancel"
        variant="warning"
        loading={cancelling}
      />
    </div>
  );
}

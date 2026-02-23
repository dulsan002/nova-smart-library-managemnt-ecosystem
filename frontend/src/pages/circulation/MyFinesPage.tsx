/**
 * MyFinesPage — list of fines with pay/waive actions.
 */

import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import { CurrencyDollarIcon } from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { MY_FINES } from '@/graphql/queries/circulation';
import { PAY_FINE } from '@/graphql/mutations/circulation';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { formatDate, formatCurrency, extractGqlError } from '@/lib/utils';

export default function MyFinesPage() {
  useDocumentTitle('Fines');

  const { data, loading, refetch } = useQuery(MY_FINES, {
    fetchPolicy: 'cache-and-network',
  });

  const fines = data?.myFines ?? [];
  const totalOutstanding = fines
    .filter((f: any) => f.status === 'PENDING' || f.status === 'OVERDUE')
    .reduce((sum: number, f: any) => sum + (f.amount ?? 0), 0);

  const [payFine, { loading: paying }] = useMutation(PAY_FINE, {
    onCompleted: () => {
      toast.success('Fine paid successfully');
      refetch();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-nova-text">My Fines</h1>
        {totalOutstanding > 0 && (
          <div className="text-right">
            <p className="text-sm text-nova-text-secondary">Outstanding</p>
            <p className="text-xl font-bold text-red-600">{formatCurrency(totalOutstanding)}</p>
          </div>
        )}
      </div>

      {loading ? (
        <LoadingOverlay />
      ) : fines.length === 0 ? (
        <EmptyState
          icon={<CurrencyDollarIcon />}
          title="No fines"
          description="You have no outstanding fines. Keep it up!"
        />
      ) : (
        <div className="space-y-3">
          {fines.map((fine: any) => {
            const statusVariant =
              fine.status === 'PAID'
                ? 'success'
                : fine.status === 'WAIVED'
                  ? 'neutral'
                  : fine.status === 'OVERDUE'
                    ? 'danger'
                    : 'warning';

            return (
              <Card key={fine.id} className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-nova-text">{fine.reason ?? 'Library Fine'}</p>
                  <p className="text-xs text-nova-text-muted">
                    Issued {formatDate(fine.createdAt)}
                    {fine.borrowRecord?.bookCopy?.book?.title && ` · ${fine.borrowRecord.bookCopy.book.title}`}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-nova-text">
                    {formatCurrency(fine.amount)}
                  </span>
                  <Badge variant={statusVariant} size="sm" dot>
                    {fine.status}
                  </Badge>
                  {(fine.status === 'PENDING' || fine.status === 'OVERDUE') && (
                    <Button
                      size="xs"
                      onClick={() => payFine({ variables: { fineId: fine.id } })}
                      isLoading={paying}
                    >
                      Pay Now
                    </Button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

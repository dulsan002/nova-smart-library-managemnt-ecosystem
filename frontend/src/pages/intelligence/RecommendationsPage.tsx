/**
 * RecommendationsPage — AI-powered book recommendations with click/dismiss.
 */

import { useQuery, useMutation } from '@apollo/client';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  SparklesIcon,
  BookOpenIcon,
  XMarkIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { MY_RECOMMENDATIONS } from '@/graphql/queries/intelligence';
import {
  GENERATE_RECOMMENDATIONS,
  CLICK_RECOMMENDATION,
  DISMISS_RECOMMENDATION,
} from '@/graphql/mutations/intelligence';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { StarRating } from '@/components/ui/StarRating';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { extractGqlError } from '@/lib/utils';

export default function RecommendationsPage() {
  useDocumentTitle('Recommendations');

  const { data, loading, refetch } = useQuery(MY_RECOMMENDATIONS, {
    variables: { limit: 20 },
    fetchPolicy: 'cache-and-network',
  });

  const recommendations = (data?.myRecommendations ?? []).filter((r: any) => r?.book);

  const [generate, { loading: generating }] = useMutation(GENERATE_RECOMMENDATIONS, {
    onCompleted: () => {
      toast.success('Fresh recommendations generated!');
      refetch();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const [clickRec] = useMutation(CLICK_RECOMMENDATION);

  const [dismissRec] = useMutation(DISMISS_RECOMMENDATION, {
    onCompleted: () => refetch(),
    onError: (err) => toast.error(extractGqlError(err)),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">
            <SparklesIcon className="mr-2 inline h-6 w-6 text-accent-500" />
            Recommendations
          </h1>
          <p className="text-sm text-nova-text-secondary">
            Personalized book suggestions powered by AI
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          leftIcon={<ArrowPathIcon className="h-4 w-4" />}
          onClick={() => generate()}
          isLoading={generating}
        >
          Refresh
        </Button>
      </div>

      {loading ? (
        <LoadingOverlay message="Loading recommendations…" />
      ) : recommendations.length === 0 ? (
        <EmptyState
          icon={<SparklesIcon />}
          title="No recommendations yet"
          description="Borrow and read some books to get personalized recommendations powered by AI."
          action={
            <Button
              onClick={() => generate()}
              isLoading={generating}
              leftIcon={<SparklesIcon className="h-4 w-4" />}
            >
              Generate Now
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {recommendations.map((rec: any) => {
            const book = rec.book;
            return (
              <Card key={rec.id} hoverable padding="none" className="group relative overflow-hidden">
                {/* Dismiss button */}
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    dismissRec({ variables: { recommendationId: rec.id } });
                  }}
                  className="absolute right-2 top-2 z-10 rounded-full bg-white/80 p-1 opacity-0 shadow transition-opacity group-hover:opacity-100 dark:bg-gray-800/80"
                  title="Dismiss"
                >
                  <XMarkIcon className="h-4 w-4 text-nova-text-muted" />
                </button>

                <Link
                  to={`/catalog/${book?.id}`}
                  onClick={() => clickRec({ variables: { recommendationId: rec.id } })}
                >
                  {/* Cover */}
                  <div className="aspect-[3/4] w-full bg-gray-100 dark:bg-gray-800">
                    {book?.coverImageUrl ? (
                      <img
                        src={book.coverImageUrl}
                        alt={book.title}
                        className="h-full w-full object-cover"
                        loading="lazy"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <BookOpenIcon className="h-12 w-12 text-gray-300" />
                      </div>
                    )}
                  </div>

                  {/* Info */}
                  <div className="p-3">
                    <h3 className="truncate text-sm font-semibold text-nova-text">
                      {book?.title}
                    </h3>
                    <p className="truncate text-xs text-nova-text-muted">
                      {book?.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ') ?? 'Unknown'}
                    </p>

                    <div className="mt-2 flex items-center gap-2">
                      <Badge variant="primary" size="xs">
                        {Math.round((rec.score ?? 0) * 100)}% match
                      </Badge>
                      {rec.explanation && (
                        <span className="truncate text-[10px] text-nova-text-muted">
                          {rec.explanation}
                        </span>
                      )}
                    </div>

                    {book?.averageRating > 0 && (
                      <div className="mt-1.5">
                        <StarRating value={book.averageRating} readonly size="sm" showLabel />
                      </div>
                    )}
                  </div>
                </Link>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

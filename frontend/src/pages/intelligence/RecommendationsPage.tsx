/**
 * RecommendationsPage — AI-powered book recommendations with click/dismiss
 * and reading preferences management.
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  SparklesIcon,
  BookOpenIcon,
  XMarkIcon,
  ArrowPathIcon,
  AdjustmentsHorizontalIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { MY_RECOMMENDATIONS, MY_PREFERENCES } from '@/graphql/queries/intelligence';
import { GET_CATEGORIES } from '@/graphql/queries/catalog';
import {
  GENERATE_RECOMMENDATIONS,
  CLICK_RECOMMENDATION,
  DISMISS_RECOMMENDATION,
  UPDATE_PREFERENCES,
} from '@/graphql/mutations/intelligence';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { StarRating } from '@/components/ui/StarRating';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { extractGqlError } from '@/lib/utils';

/* ─── Language options ───────────────────── */
const LANGUAGES = [
  'English', 'Sinhala', 'Tamil', 'French', 'Spanish', 'German',
  'Chinese', 'Japanese', 'Korean', 'Arabic', 'Hindi', 'Portuguese',
];

export default function RecommendationsPage() {
  useDocumentTitle('Recommendations');

  const [showPrefs, setShowPrefs] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);

  const { data, loading, refetch } = useQuery(MY_RECOMMENDATIONS, {
    variables: { limit: 20 },
    fetchPolicy: 'cache-and-network',
  });

  const { data: prefData } = useQuery(MY_PREFERENCES);
  const { data: catData } = useQuery(GET_CATEGORIES, { variables: { rootOnly: true } });

  const recommendations = (data?.myRecommendations ?? []).filter((r: any) => r?.book);
  const categories = catData?.categories ?? [];

  // Sync preferences from server
  useEffect(() => {
    if (prefData?.myPreferences) {
      setSelectedCategories(prefData.myPreferences.preferredCategories ?? []);
      setSelectedLanguages(prefData.myPreferences.preferredLanguages ?? []);
    }
  }, [prefData]);

  const [generate, { loading: generating }] = useMutation(GENERATE_RECOMMENDATIONS, {
    onCompleted: () => {
      toast.success('Fresh recommendations generated!');
      refetch();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const [updatePreferences, { loading: savingPrefs }] = useMutation(UPDATE_PREFERENCES, {
    onCompleted: () => {
      toast.success('Preferences saved successfully!');
      setShowPrefs(false);
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
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            leftIcon={<AdjustmentsHorizontalIcon className="h-4 w-4" />}
            onClick={() => setShowPrefs((v) => !v)}
          >
            Preferences
          </Button>
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
      </div>

      {/* ─── Preferences Panel ─── */}
      {showPrefs && (
        <Card className="border-primary-200 dark:border-primary-800 bg-primary-50/30 dark:bg-primary-900/10">
          <div className="space-y-5">
            <h3 className="text-sm font-bold text-nova-text flex items-center gap-2">
              <AdjustmentsHorizontalIcon className="h-4 w-4 text-primary-500" />
              Reading Preferences
            </h3>

            {/* Preferred Categories */}
            <div>
              <label className="block text-xs font-semibold text-nova-text-muted uppercase tracking-wider mb-2">
                Preferred Categories
              </label>
              <div className="flex flex-wrap gap-2">
                {categories.length > 0 ? categories.map((cat: any) => {
                  const isSelected = selectedCategories.includes(cat.name);
                  return (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() =>
                        setSelectedCategories((prev) =>
                          isSelected ? prev.filter((c) => c !== cat.name) : [...prev, cat.name],
                        )
                      }
                      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all ${
                        isSelected
                          ? 'bg-primary-600 text-white shadow-sm'
                          : 'bg-nova-surface border border-nova-border text-nova-text-muted hover:border-primary-400 hover:text-primary-600'
                      }`}
                    >
                      {cat.icon && <span>{cat.icon}</span>}
                      {cat.name}
                      {isSelected && <CheckIcon className="h-3 w-3" />}
                    </button>
                  );
                }) : (
                  ['Fiction', 'Non-Fiction', 'Science', 'Technology', 'Databases', 'Mathematics',
                   'History', 'Philosophy', 'Literature', 'Computer Science', 'Engineering', 'Arts',
                  ].map((name) => {
                    const isSelected = selectedCategories.includes(name);
                    return (
                      <button
                        key={name}
                        type="button"
                        onClick={() =>
                          setSelectedCategories((prev) =>
                            isSelected ? prev.filter((c) => c !== name) : [...prev, name],
                          )
                        }
                        className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all ${
                          isSelected
                            ? 'bg-primary-600 text-white shadow-sm'
                            : 'bg-nova-surface border border-nova-border text-nova-text-muted hover:border-primary-400 hover:text-primary-600'
                        }`}
                      >
                        {name}
                        {isSelected && <CheckIcon className="h-3 w-3" />}
                      </button>
                    );
                  })
                )}
              </div>
            </div>

            {/* Preferred Languages */}
            <div>
              <label className="block text-xs font-semibold text-nova-text-muted uppercase tracking-wider mb-2">
                Preferred Languages
              </label>
              <div className="flex flex-wrap gap-2">
                {LANGUAGES.map((lang) => {
                  const isSelected = selectedLanguages.includes(lang);
                  return (
                    <button
                      key={lang}
                      type="button"
                      onClick={() =>
                        setSelectedLanguages((prev) =>
                          isSelected ? prev.filter((l) => l !== lang) : [...prev, lang],
                        )
                      }
                      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all ${
                        isSelected
                          ? 'bg-accent-600 text-white shadow-sm'
                          : 'bg-nova-surface border border-nova-border text-nova-text-muted hover:border-accent-400 hover:text-accent-600'
                      }`}
                    >
                      {lang}
                      {isSelected && <CheckIcon className="h-3 w-3" />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Current selections summary + save */}
            <div className="flex items-center justify-between pt-2 border-t border-nova-border">
              <p className="text-xs text-nova-text-muted">
                {selectedCategories.length} categories · {selectedLanguages.length} languages selected
              </p>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => setShowPrefs(false)}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  isLoading={savingPrefs}
                  onClick={() =>
                    updatePreferences({
                      variables: {
                        preferredCategories: selectedCategories,
                        preferredLanguages: selectedLanguages,
                      },
                    })
                  }
                >
                  Save Preferences
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

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

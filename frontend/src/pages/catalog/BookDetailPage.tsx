/**
 * BookDetailPage — Comprehensive book detail view inspired by NYPL catalog.
 *
 * Features:
 * - Breadcrumb navigation
 * - Format availability tabs (Book | eBook | eAudiobook)
 * - Per-branch/location availability with status indicators
 * - Rich author profiles
 * - Related books carousel
 * - Reservation system with queue tracking
 * - User review submission
 *
 * Users can RESERVE books (not borrow directly).
 */

import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  BookOpenIcon,
  CalendarDaysIcon,
  LanguageIcon,
  HashtagIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  UserGroupIcon,
  MapPinIcon,
  ShieldExclamationIcon,
  MusicalNoteIcon,
  DocumentTextIcon,
  UserIcon,
  GlobeAltIcon,
  AcademicCapIcon,
  ArrowTopRightOnSquareIcon,
  ChevronRightIcon,
  HomeIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { GET_BOOK, GET_AUTHOR, GET_BOOKS } from '@/graphql/queries/catalog';
import { DIGITAL_ASSETS_FOR_BOOK } from '@/graphql/queries/digital';
import { MY_RESERVATIONS, MY_RESERVATION_BAN, MY_BORROWS } from '@/graphql/queries/circulation';
import { RESERVE_BOOK, CANCEL_RESERVATION } from '@/graphql/mutations/circulation';
import { SUBMIT_BOOK_REVIEW } from '@/graphql/mutations/catalog';
import { LOG_BOOK_VIEW } from '@/graphql/mutations/intelligence';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { StarRating } from '@/components/ui/StarRating';
import { Tabs } from '@/components/ui/Tabs';
import { Textarea } from '@/components/ui/Textarea';
import { LoadingScreen } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatDate, extractGqlError } from '@/lib/utils';

export default function BookDetailPage() {
  const { bookId } = useParams<{ bookId: string }>();

  const { data, loading, refetch } = useQuery(GET_BOOK, {
    variables: { id: bookId },
    skip: !bookId,
  });

  const { data: assetsData } = useQuery(DIGITAL_ASSETS_FOR_BOOK, {
    variables: { bookId },
    skip: !bookId,
  });

  const { data: reservationsData, refetch: refetchReservations } = useQuery(MY_RESERVATIONS);
  const { data: banData } = useQuery(MY_RESERVATION_BAN);
  const { data: borrowsData } = useQuery(MY_BORROWS, {
    variables: { status: 'ACTIVE' },
  });

  const book = data?.book;
  const primaryAuthor = book?.authors?.[0];

  /* ─── Limits: max 2 borrows, max 2 reservations ─── */
  const MAX_BORROWS = 2;
  const MAX_RESERVATIONS = 2;
  const activeBorrows = (borrowsData?.myBorrows ?? []).filter(
    (b: any) => b.status === 'ACTIVE' || b.status === 'OVERDUE',
  ).length;
  const activeReservations = (reservationsData?.myReservations ?? []).filter(
    (r: any) => r.status === 'PENDING' || r.status === 'READY',
  ).length;
  const canReserve = activeBorrows < MAX_BORROWS && activeReservations < MAX_RESERVATIONS;

  /* ─── Author detail query ─── */
  const { data: authorData } = useQuery(GET_AUTHOR, {
    variables: { id: primaryAuthor?.id },
    skip: !primaryAuthor?.id,
  });
  const author = authorData?.author;

  /* ─── Author's other books ─── */
  const { data: authorBooksData } = useQuery(GET_BOOKS, {
    variables: { authorId: primaryAuthor?.id, first: 12 },
    skip: !primaryAuthor?.id,
  });
  const authorBooks = (authorBooksData?.books?.edges ?? [])
    .map((e: any) => e.node)
    .filter((b: any) => b && b.id !== bookId);
  useDocumentTitle(book?.title ?? 'Book Details');

  // Track book view for browse-based recommendations
  const [logBookView] = useMutation(LOG_BOOK_VIEW);
  const viewStartRef = useRef(Date.now());
  const viewLoggedRef = useRef(false);

  useEffect(() => {
    if (!bookId || viewLoggedRef.current) return;
    viewLoggedRef.current = true;
    viewStartRef.current = Date.now();
    logBookView({ variables: { bookId, source: 'catalog' } }).catch(() => {});

    // On unmount, update duration
    return () => {
      const duration = Math.round((Date.now() - viewStartRef.current) / 1000);
      if (duration > 3) {
        logBookView({
          variables: { bookId, source: 'catalog', durationSeconds: duration },
        }).catch(() => {});
      }
    };
  }, [bookId, logBookView]);

  // Find if user already has an active reservation for this book
  const myReservation = (reservationsData?.myReservations ?? []).find(
    (r: any) => r.book?.id === bookId && ['PENDING', 'READY'].includes(r.status),
  );

  const isBanned = banData?.myReservationBan?.isActive === true;
  const banInfo = banData?.myReservationBan;

  const [reserveBook, { loading: reserving }] = useMutation(RESERVE_BOOK, {
    onCompleted: (data) => {
      const resv = data.reserveBook;
      if (resv.status === 'READY') {
        toast.success(
          `Reserved! Pick up within 12 hours.\nLocation: ${resv.pickupLocation || 'Check at desk'}`,
          { duration: 6000 },
        );
      } else {
        toast.success(`Added to queue (position #${resv.queuePosition}). We'll notify you when a copy is ready.`);
      }
      refetch();
      refetchReservations();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const [cancelReservation, { loading: cancelling }] = useMutation(CANCEL_RESERVATION, {
    onCompleted: () => {
      toast.success('Reservation cancelled.');
      refetch();
      refetchReservations();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  if (loading) return <LoadingScreen />;
  if (!book) {
    return (
      <EmptyState
        icon={<BookOpenIcon />}
        title="Book not found"
        description="The requested book could not be found."
        action={
          <Link to="/catalog">
            <Button>Back to Catalog</Button>
          </Link>
        }
      />
    );
  }

  const copies = book.copies ?? [];
  const availableCopies = copies.filter((c: any) => c.status === 'AVAILABLE');
  const reviews = book.reviews ?? [];
  const digitalAssets = assetsData?.digitalAssetsForBook ?? [];
  const ebooks = digitalAssets.filter((a: any) => a.assetType === 'EBOOK');
  const audiobooks = digitalAssets.filter((a: any) => a.assetType === 'AUDIOBOOK');

  function handleReserve() {
    reserveBook({ variables: { bookId: book.id } });
  }

  function handleCancelReservation() {
    if (myReservation) {
      cancelReservation({ variables: { reservationId: myReservation.id } });
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Breadcrumb Navigation */}
      <nav className="flex items-center gap-1.5 text-sm text-nova-text-muted">
        <Link to="/" className="flex items-center gap-1 hover:text-primary-600 transition-colors">
          <HomeIcon className="h-4 w-4" />
          <span>Home</span>
        </Link>
        <ChevronRightIcon className="h-3 w-3" />
        <Link to="/catalog" className="hover:text-primary-600 transition-colors">
          Catalog
        </Link>
        {book.categories?.[0] && (
          <>
            <ChevronRightIcon className="h-3 w-3" />
            <Link
              to={`/catalog?category=${book.categories[0].id}`}
              className="hover:text-primary-600 transition-colors"
            >
              {book.categories[0].name}
            </Link>
          </>
        )}
        <ChevronRightIcon className="h-3 w-3" />
        <span className="font-medium text-nova-text truncate max-w-[200px]">{book.title}</span>
      </nav>

      {/* Ban warning */}
      {isBanned && banInfo && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/30">
          <ShieldExclamationIcon className="h-6 w-6 flex-shrink-0 text-red-500" />
          <div>
            <p className="font-semibold text-red-700 dark:text-red-400">Reservation Temporarily Suspended</p>
            <p className="mt-1 text-sm text-red-600 dark:text-red-400/80">
              {banInfo.reason}
            </p>
            <p className="mt-1 text-xs text-red-500">
              Ban expires: {formatDate(banInfo.expiresAt)}
            </p>
          </div>
        </div>
      )}

      {/* Hero section */}
      <div className="flex flex-col gap-8 lg:flex-row">
        {/* Cover */}
        <div className="flex-shrink-0">
          <div className="relative h-80 w-56 overflow-hidden rounded-2xl bg-gray-100 shadow-lg dark:bg-gray-800 lg:h-96 lg:w-64">
            {book.coverImageUrl ? (
              <img
                src={book.coverImageUrl}
                alt={book.title}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <BookOpenIcon className="h-16 w-16 text-gray-300 dark:text-gray-600" />
              </div>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="flex-1 space-y-4">
          <div>
            <h1 className="text-3xl font-bold text-nova-text">{book.title}</h1>
            {book.subtitle && (
              <p className="mt-1 text-lg text-nova-text-secondary">{book.subtitle}</p>
            )}
            <p className="mt-2 text-nova-text-secondary">
              by{' '}
              {book.authors?.map((a: any, i: number) => (
                <span key={a.id}>
                  {i > 0 && ', '}
                  <span className="font-medium text-nova-text">{a.firstName} {a.lastName}</span>
                </span>
              ))}
            </p>
          </div>

          {/* Rating */}
          {Number(book.averageRating) > 0 && (
            <div className="flex items-center gap-2">
              <StarRating value={Number(book.averageRating)} readonly size="md" />
              <span className="text-sm font-medium text-nova-text">
                {Number(book.averageRating).toFixed(1)}
              </span>
              <span className="text-sm text-nova-text-muted">
                ({reviews.length} review{reviews.length !== 1 ? 's' : ''})
              </span>
            </div>
          )}

          {/* Meta grid */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetaItem
              icon={<CalendarDaysIcon className="h-4 w-4" />}
              label="Published"
              value={book.publicationDate ? formatDate(book.publicationDate) : 'N/A'}
            />
            <MetaItem
              icon={<LanguageIcon className="h-4 w-4" />}
              label="Language"
              value={book.language ?? 'N/A'}
            />
            <MetaItem
              icon={<HashtagIcon className="h-4 w-4" />}
              label="ISBN"
              value={book.isbn13 ?? book.isbn10 ?? 'N/A'}
            />
            <MetaItem
              icon={<ClipboardDocumentListIcon className="h-4 w-4" />}
              label="Pages"
              value={book.pageCount ?? 'N/A'}
            />
          </div>

          {/* Categories */}
          {book.categories?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {book.categories.map((c: any) => (
                <Badge key={c.id} variant="primary" size="sm">
                  {c.name}
                </Badge>
              ))}
            </div>
          )}

          {/* Availability & Actions */}
          <div className="space-y-3 pt-2">
            {/* Format availability row */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Physical copies */}
              <div className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium border ${
                availableCopies.length > 0
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400'
                  : 'border-red-200 bg-red-50 text-red-600 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400'
              }`}>
                <BookOpenIcon className="h-4 w-4" />
                <span>
                  {availableCopies.length > 0
                    ? `${availableCopies.length} of ${copies.length} copies available`
                    : `All ${copies.length} copies checked out`}
                </span>
              </div>
              {/* E-book badge */}
              {ebooks.length > 0 && (
                <div className="inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                  <DocumentTextIcon className="h-4 w-4" />
                  <span>E-Book Available</span>
                </div>
              )}
              {/* Audiobook badge */}
              {audiobooks.length > 0 && (
                <div className="inline-flex items-center gap-2 rounded-lg border border-violet-200 bg-violet-50 px-3 py-2 text-sm font-medium text-violet-700 dark:border-violet-800 dark:bg-violet-900/20 dark:text-violet-400">
                  <MusicalNoteIcon className="h-4 w-4" />
                  <span>Audiobook Available</span>
                </div>
              )}
            </div>

            {/* Reservation status or action */}
            {myReservation ? (
              <ReservationStatusCard
                reservation={myReservation}
                onCancel={handleCancelReservation}
                cancelling={cancelling}
              />
            ) : (
              <div className="space-y-3">
                {!canReserve && (
                  <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 dark:border-amber-600 dark:bg-amber-900/30">
                    <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                      Borrowing limit reached
                    </p>
                    <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
                      You have {activeBorrows}/{MAX_BORROWS} active borrows and {activeReservations}/{MAX_RESERVATIONS} reservations.
                      {activeBorrows >= MAX_BORROWS && ' Return a book to borrow more.'}
                      {activeReservations >= MAX_RESERVATIONS && ' Cancel or pick up a reservation to reserve more.'}
                    </p>
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    leftIcon={<ClockIcon className="h-4 w-4" />}
                    onClick={handleReserve}
                    isLoading={reserving}
                    disabled={isBanned || !canReserve}
                  >
                    {availableCopies.length > 0 ? 'Reserve a Copy' : 'Join Waitlist'}
                  </Button>

                  {ebooks.length > 0 && (
                    <Link to={`/reader/${ebooks[0].id}`}>
                      <Button variant="secondary" leftIcon={<BookOpenIcon className="h-4 w-4" />}>
                        Read Online
                      </Button>
                    </Link>
                  )}

                  {audiobooks.length > 0 && (
                    <Link to={`/listen/${audiobooks[0].id}`}>
                      <Button variant="secondary" leftIcon={<MusicalNoteIcon className="h-4 w-4" />}>
                        Listen
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* How it works info */}
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/50">
            <p className="text-xs font-semibold text-nova-text-muted uppercase tracking-wide mb-2">
              How borrowing works
            </p>
            <ol className="text-xs text-nova-text-secondary space-y-1 list-decimal list-inside">
              <li>Reserve a copy through the app</li>
              <li>If available, pick up within <strong>12 hours</strong> at the indicated location</li>
              <li>If no copies are available, you'll be placed in a queue</li>
              <li>Return the book physically at the library</li>
              <li>Renew via the app if no one else is waiting</li>
            </ol>
            <p className="text-xs text-nova-text-muted mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
              <strong>Limits:</strong> Max {MAX_BORROWS} active borrows &amp; {MAX_RESERVATIONS} reservations at a time.
            </p>
          </div>
        </div>
      </div>

      {/* 360° Tabs: Description, Author, Digital, Reviews, Copies */}
      <Tabs
        tabs={[
          {
            label: 'Description',
            content: (
              <div className="nova-prose max-w-none space-y-6">
                {book.description ? (
                  <p className="whitespace-pre-line text-nova-text-secondary leading-relaxed">
                    {book.description}
                  </p>
                ) : (
                  <p className="text-nova-text-muted italic">No description available.</p>
                )}
                {book.tableOfContents && (
                  <div>
                    <h3 className="text-lg font-semibold text-nova-text mb-3">Table of Contents</h3>
                    <div className="rounded-xl border border-nova-border bg-nova-surface p-4">
                      <p className="whitespace-pre-line text-sm text-nova-text-secondary">
                        {book.tableOfContents}
                      </p>
                    </div>
                  </div>
                )}
                {(() => {
                  const tags = Array.isArray(book.tags)
                    ? book.tags
                    : typeof book.tags === 'string'
                      ? (() => { try { const p = JSON.parse(book.tags); return Array.isArray(p) ? p : []; } catch { return []; } })()
                      : [];
                  return tags.length > 0 ? (
                    <div>
                      <h3 className="text-lg font-semibold text-nova-text mb-3">Tags</h3>
                      <div className="flex flex-wrap gap-2">
                        {tags.map((tag: string, i: number) => (
                          <Badge key={i} variant="primary" size="sm">{tag}</Badge>
                        ))}
                      </div>
                    </div>
                  ) : null;
                })()}
                {/* Additional book metadata */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {book.publisher && (
                    <div className="rounded-xl border border-nova-border bg-nova-surface p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-nova-text-muted mb-1">Publisher</p>
                      <p className="text-sm font-medium text-nova-text">{book.publisher}</p>
                    </div>
                  )}
                  {book.edition && (
                    <div className="rounded-xl border border-nova-border bg-nova-surface p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-nova-text-muted mb-1">Edition</p>
                      <p className="text-sm font-medium text-nova-text">{book.edition}</p>
                    </div>
                  )}
                  {(book.deweyDecimal || book.lccNumber) && (
                    <div className="rounded-xl border border-nova-border bg-nova-surface p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-nova-text-muted mb-1">Classification</p>
                      <p className="text-sm font-medium text-nova-text">
                        {book.deweyDecimal && `Dewey: ${book.deweyDecimal}`}
                        {book.deweyDecimal && book.lccNumber && ' | '}
                        {book.lccNumber && `LCC: ${book.lccNumber}`}
                      </p>
                    </div>
                  )}
                  <div className="rounded-xl border border-nova-border bg-nova-surface p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-nova-text-muted mb-1">Statistics</p>
                    <p className="text-sm font-medium text-nova-text">
                      {book.totalBorrows ?? 0} borrows
                    </p>
                  </div>
                </div>
              </div>
            ),
          },
          {
            label: 'Author',
            content: (
              <AuthorSection
                author={author}
                authors={book.authors}
                authorBooks={authorBooks}
              />
            ),
          },
          {
            label: 'Digital',
            badge: digitalAssets.length,
            content: (
              <DigitalContentSection
                ebooks={ebooks}
                audiobooks={audiobooks}
              />
            ),
          },
          {
            label: 'Reviews',
            badge: reviews.length,
            content: <ReviewsSection bookId={book.id} reviews={reviews} onSubmit={refetch} />,
          },
          {
            label: 'Copies',
            badge: copies.length,
            content: (
              <div className="space-y-3">
                {copies.length === 0 ? (
                  <EmptyState title="No copies" description="No physical copies registered." />
                ) : (
                  copies.map((copy: any) => (
                    <Card key={copy.id} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-nova-text">
                          Copy #{copy.barcode ?? copy.id.slice(-6)}
                        </p>
                        <p className="text-xs text-nova-text-muted flex items-center gap-1">
                          <MapPinIcon className="h-3 w-3" />
                          {copy.floorNumber != null && `Floor ${copy.floorNumber}`}
                          {copy.floorNumber != null && copy.shelfNumber && ', '}
                          {copy.shelfNumber && `Shelf ${copy.shelfNumber}`}
                          {!copy.floorNumber && !copy.shelfNumber && (copy.shelfLocation || 'Main Library')}
                        </p>
                      </div>
                      <Badge
                        variant={copy.status === 'AVAILABLE' ? 'success' : copy.status === 'RESERVED' ? 'warning' : 'danger'}
                        size="sm"
                      >
                        {copy.status}
                      </Badge>
                    </Card>
                  ))
                )}
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}

/* ---------- ReservationStatusCard ---------- */

function ReservationStatusCard({
  reservation,
  onCancel,
  cancelling,
}: {
  reservation: any;
  onCancel: () => void;
  cancelling: boolean;
}) {
  const isReady = reservation.status === 'READY';
  const hours = reservation.hoursUntilExpiry;

  return (
    <div
      className={`rounded-xl border p-4 ${
        isReady
          ? 'border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950/30'
          : 'border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950/30'
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className={`font-semibold ${isReady ? 'text-green-700 dark:text-green-400' : 'text-blue-700 dark:text-blue-400'}`}>
            {isReady ? 'Ready for Pickup!' : `In Queue — Position #${reservation.queuePosition}`}
          </p>
          {isReady && (
            <>
              <p className="mt-1 text-sm text-green-600 dark:text-green-400/80">
                <MapPinIcon className="inline h-4 w-4 mr-1" />
                Pickup at: <strong>{reservation.pickupLocation || 'Library Desk'}</strong>
              </p>
              <p className="mt-1 text-sm text-green-600 dark:text-green-400/80">
                <ClockIcon className="inline h-4 w-4 mr-1" />
                {hours > 0
                  ? `${hours.toFixed(1)} hours remaining to pick up`
                  : 'Pickup deadline has passed'}
              </p>
              <p className="mt-1 text-xs text-green-500">
                Expires: {formatDate(reservation.expiresAt)}
              </p>
            </>
          )}
          {!isReady && (
            <p className="mt-1 text-sm text-blue-600 dark:text-blue-400/80">
              We'll notify you when a copy is available for pickup.
            </p>
          )}
        </div>
        <Button
          variant="outline"
          size="xs"
          onClick={onCancel}
          isLoading={cancelling}
        >
          Cancel
        </Button>
      </div>
    </div>
  );
}

/* ---------- ReviewsSection ---------- */

function ReviewsSection({
  bookId,
  reviews,
  onSubmit,
}: {
  bookId: string;
  reviews: any[];
  onSubmit: () => void;
}) {
  const [rating, setRating] = useState(0);
  const [content, setContent] = useState('');

  const [submitReview, { loading }] = useMutation(SUBMIT_BOOK_REVIEW, {
    onCompleted: () => {
      toast.success('Review submitted!');
      setRating(0);
      setContent('');
      onSubmit();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (rating === 0) {
      toast.error('Please select a rating');
      return;
    }
    submitReview({ variables: { bookId, rating: Number(rating), content: content || '' } });
  }

  return (
    <div className="space-y-6">
      {/* Write review */}
      <Card>
        <CardHeader title="Write a Review" />
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <p className="mb-1 text-sm text-nova-text-secondary">Your rating</p>
            <StarRating value={rating} onChange={setRating} size="lg" />
          </div>
          <Textarea
            name="review"
            placeholder="Share your thoughts about this book…"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={3}
          />
          <Button type="submit" size="sm" isLoading={loading} disabled={rating === 0}>
            Submit Review
          </Button>
        </form>
      </Card>

      {/* Reviews list */}
      {reviews.length === 0 ? (
        <EmptyState
          icon={<UserGroupIcon />}
          title="No reviews yet"
          description="Be the first to review this book."
        />
      ) : (
        <div className="space-y-4">
          {reviews.map((review: any) => (
            <Card key={review.id}>
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-nova-text">
                      {review.user?.firstName} {review.user?.lastName}
                    </span>
                    <StarRating value={review.rating} readonly size="sm" />
                  </div>
                  {review.content && (
                    <p className="mt-1.5 text-sm text-nova-text-secondary">
                      {review.content}
                    </p>
                  )}
                  <p className="mt-2 text-xs text-nova-text-muted">
                    {formatDate(review.createdAt)}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------- AuthorSection ---------- */

function AuthorSection({
  author,
  authors,
  authorBooks,
}: {
  author: any;
  authors: any[];
  authorBooks: any[];
}) {
  const displayAuthor = author ?? authors?.[0];

  if (!displayAuthor) {
    return (
      <EmptyState
        icon={<UserIcon />}
        title="No author information"
        description="Author details are not available for this book."
      />
    );
  }

  return (
    <div className="space-y-8">
      {/* Author profile */}
      <div className="flex flex-col gap-6 sm:flex-row">
        {/* Photo */}
        <div className="flex-shrink-0">
          <div className="h-32 w-32 overflow-hidden rounded-2xl bg-gray-100 shadow-md dark:bg-gray-800">
            {author?.photoUrl ? (
              <img
                src={author.photoUrl}
                alt={`${displayAuthor.firstName} ${displayAuthor.lastName}`}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <UserIcon className="h-12 w-12 text-gray-300 dark:text-gray-600" />
              </div>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="flex-1 space-y-3">
          <h3 className="text-2xl font-bold text-nova-text">
            {displayAuthor.firstName} {displayAuthor.lastName}
          </h3>
          <div className="flex flex-wrap gap-3">
            {author?.nationality && (
              <div className="flex items-center gap-1.5 text-sm text-nova-text-secondary">
                <GlobeAltIcon className="h-4 w-4 text-nova-text-muted" />
                {author.nationality}
              </div>
            )}
            {author?.birthDate && (
              <div className="flex items-center gap-1.5 text-sm text-nova-text-secondary">
                <CalendarDaysIcon className="h-4 w-4 text-nova-text-muted" />
                Born {formatDate(author.birthDate)}
                {author.deathDate && ` — Died ${formatDate(author.deathDate)}`}
              </div>
            )}
          </div>
          {author?.biography ? (
            <p className="text-sm text-nova-text-secondary leading-relaxed whitespace-pre-line">
              {author.biography}
            </p>
          ) : (
            <p className="text-sm text-nova-text-muted italic">
              No biography available for this author.
            </p>
          )}
        </div>
      </div>

      {/* Other authors (if multi-author book) */}
      {authors?.length > 1 && (
        <div>
          <h4 className="text-base font-semibold text-nova-text mb-3">All Authors</h4>
          <div className="flex flex-wrap gap-3">
            {authors.map((a: any) => (
              <div
                key={a.id}
                className="flex items-center gap-2 rounded-xl border border-nova-border bg-nova-surface px-3 py-2"
              >
                <UserIcon className="h-4 w-4 text-nova-text-muted" />
                <span className="text-sm font-medium text-nova-text">
                  {a.firstName} {a.lastName}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Other books by this author */}
      {authorBooks.length > 0 && (
        <div>
          <h4 className="text-base font-semibold text-nova-text mb-4">
            More by {displayAuthor.firstName} {displayAuthor.lastName}
          </h4>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
            {authorBooks.map((b: any) => (
              <Link key={b.id} to={`/catalog/${b.id}`} className="group">
                <div className="overflow-hidden rounded-xl border border-nova-border bg-nova-surface shadow-sm transition-all hover:shadow-md hover:border-primary-300 dark:hover:border-primary-700">
                  <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-800">
                    {b.coverImageUrl ? (
                      <img
                        src={b.coverImageUrl}
                        alt={b.title}
                        className="h-full w-full object-cover transition-transform group-hover:scale-105"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <BookOpenIcon className="h-8 w-8 text-gray-300 dark:text-gray-600" />
                      </div>
                    )}
                  </div>
                  <div className="p-2.5">
                    <p className="text-xs font-semibold text-nova-text line-clamp-2 leading-tight">
                      {b.title}
                    </p>
                    {Number(b.averageRating) > 0 && (
                      <div className="mt-1 flex items-center gap-1">
                        <StarRating value={Number(b.averageRating)} readonly size="sm" />
                        <span className="text-[10px] text-nova-text-muted">
                          {Number(b.averageRating).toFixed(1)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {authorBooks.length === 0 && (
        <Card className="text-center py-6">
          <AcademicCapIcon className="mx-auto h-8 w-8 text-nova-text-muted mb-2" />
          <p className="text-sm text-nova-text-muted">
            No other books by this author in our collection.
          </p>
        </Card>
      )}
    </div>
  );
}

/* ---------- DigitalContentSection ---------- */

function DigitalContentSection({
  ebooks,
  audiobooks,
}: {
  ebooks: any[];
  audiobooks: any[];
}) {
  if (ebooks.length === 0 && audiobooks.length === 0) {
    return (
      <EmptyState
        icon={<DocumentTextIcon />}
        title="No digital content"
        description="This book doesn't have any digital formats available yet."
      />
    );
  }

  function formatFileSize(bytes: number): string {
    if (!bytes) return 'N/A';
    if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
    if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(1)} MB`;
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${bytes} B`;
  }

  function formatDuration(seconds: number): string {
    if (!seconds) return 'N/A';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  }

  return (
    <div className="space-y-6">
      {/* E-books */}
      {ebooks.length > 0 && (
        <div>
          <h4 className="flex items-center gap-2 text-base font-semibold text-nova-text mb-3">
            <BookOpenIcon className="h-5 w-5 text-primary-500" />
            E-Books ({ebooks.length})
          </h4>
          <div className="space-y-3">
            {ebooks.map((asset: any) => (
              <Card key={asset.id} className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400">
                    <BookOpenIcon className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-nova-text">
                      E-Book
                      {asset.mimeType && (
                        <span className="ml-2 text-xs font-normal text-nova-text-muted">
                          ({asset.mimeType.split('/').pop()?.toUpperCase()})
                        </span>
                      )}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-nova-text-muted mt-0.5">
                      {asset.totalPages && <span>{asset.totalPages} pages</span>}
                      {asset.fileSizeBytes && <span>{formatFileSize(asset.fileSizeBytes)}</span>}
                    </div>
                  </div>
                </div>
                <Link to={`/reader/${asset.id}`}>
                  <Button size="sm" leftIcon={<ArrowTopRightOnSquareIcon className="h-4 w-4" />}>
                    Read Now
                  </Button>
                </Link>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Audiobooks */}
      {audiobooks.length > 0 && (
        <div>
          <h4 className="flex items-center gap-2 text-base font-semibold text-nova-text mb-3">
            <MusicalNoteIcon className="h-5 w-5 text-violet-500" />
            Audiobooks ({audiobooks.length})
          </h4>
          <div className="space-y-3">
            {audiobooks.map((asset: any) => (
              <Card key={asset.id} className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-50 text-violet-600 dark:bg-violet-900/20 dark:text-violet-400">
                    <MusicalNoteIcon className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-nova-text">
                      Audiobook
                      {asset.narrator && (
                        <span className="ml-2 text-xs font-normal text-nova-text-muted">
                          Narrated by {asset.narrator}
                        </span>
                      )}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-nova-text-muted mt-0.5">
                      {asset.durationSeconds && <span>{formatDuration(asset.durationSeconds)}</span>}
                      {asset.fileSizeBytes && <span>{formatFileSize(asset.fileSizeBytes)}</span>}
                    </div>
                  </div>
                </div>
                <Link to={`/listen/${asset.id}`}>
                  <Button size="sm" variant="secondary" leftIcon={<MusicalNoteIcon className="h-4 w-4" />}>
                    Listen Now
                  </Button>
                </Link>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- MetaItem ---------- */

function MetaItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-nova-text-muted">{icon}</span>
      <div>
        <p className="text-xs text-nova-text-muted">{label}</p>
        <p className="font-medium text-nova-text">{value}</p>
      </div>
    </div>
  );
}

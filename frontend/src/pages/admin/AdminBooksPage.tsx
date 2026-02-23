/**
 * AdminBooksPage — Premium enterprise book management with 360° panoramic view,
 * create/edit with validation, copy management, icon action buttons.
 */

import { useState, useCallback } from 'react';
import { useQuery, useLazyQuery, useMutation } from '@apollo/client';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import {
  PlusCircleIcon,
  PencilSquareIcon,
  MagnifyingGlassIcon,
  SquaresPlusIcon,
  EyeIcon,
  DocumentDuplicateIcon,
  ChatBubbleLeftRightIcon,
  StarIcon,
  ArrowPathIcon,
  InformationCircleIcon,
  EllipsisVerticalIcon,
  BookOpenIcon,
  TagIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle, useDebounce } from '@/hooks';
import { GET_BOOKS, GET_BOOK, GET_AUTHORS } from '@/graphql/queries/catalog';
import { CREATE_BOOK, UPDATE_BOOK, ADD_BOOK_COPY, DELETE_BOOK } from '@/graphql/mutations/catalog';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';
import { Modal, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { Tabs } from '@/components/ui/Tabs';
import { Tooltip } from '@/components/ui/Tooltip';
import { Dropdown } from '@/components/ui/Dropdown';
import { Pagination } from '@/components/ui/Pagination';
import { LoadingOverlay, Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { extractGqlError, formatDate } from '@/lib/utils';
import { ITEMS_PER_PAGE, BOOK_LANGUAGES } from '@/lib/constants';

/* === Schemas === */

const bookSchema = z.object({
  title: z.string().min(1, 'Required'),
  subtitle: z.string().optional(),
  isbn13: z.string().optional(),
  isbn10: z.string().optional(),
  publisher: z.string().optional(),
  language: z.string().optional(),
  pageCount: z.string().optional(),
  description: z.string().optional(),
  coverImageUrl: z.string().url('Must be a valid URL').optional().or(z.literal('')),
});
type BookForm = z.infer<typeof bookSchema>;

const copySchema = z.object({
  barcode: z.string().min(1, 'Required'),
  shelfLocation: z.string().optional(),
  branch: z.string().optional(),
  condition: z.string().optional(),
});
type CopyForm = z.infer<typeof copySchema>;

/* === Helpers === */

const copyStatusColor = (s: string) => {
  switch (s) {
    case 'AVAILABLE': return 'success';
    case 'BORROWED': return 'warning';
    case 'RESERVED': return 'info';
    case 'MAINTENANCE': return 'neutral';
    case 'LOST': case 'DAMAGED': return 'danger';
    default: return 'neutral';
  }
};

const conditionColor = (c: string) => {
  switch (c) {
    case 'NEW': return 'success';
    case 'GOOD': return 'info';
    case 'FAIR': return 'warning';
    case 'POOR': case 'DAMAGED': return 'danger';
    default: return 'neutral';
  }
};

const langOptions = [
  { value: '', label: 'All languages' },
  ...BOOK_LANGUAGES.map((l) => ({ value: l.code, label: l.label })),
];

/* === Main Component === */

export default function AdminBooksPage() {
  useDocumentTitle('Manage Books');

  const [search, setSearch] = useState('');
  const [after, setAfter] = useState<string | null>(null);
  const [langFilter, setLangFilter] = useState('');
  const debouncedSearch = useDebounce(search, 400);

  const [showBookModal, setShowBookModal] = useState(false);
  const [editingBook, setEditingBook] = useState<any | null>(null);
  const [showCopyModal, setShowCopyModal] = useState<string | null>(null);
  const [viewBookId, setViewBookId] = useState<string | null>(null);
  const [viewTab, setViewTab] = useState(0);
  const [selectedAuthorIds, setSelectedAuthorIds] = useState<string[]>([]);
  const [deleteTarget, setDeleteTarget] = useState<any | null>(null);

  const { data, loading, refetch } = useQuery(GET_BOOKS, {
    variables: {
      first: ITEMS_PER_PAGE,
      after,
      query: debouncedSearch || undefined,
      language: langFilter || undefined,
    },
    fetchPolicy: 'cache-and-network',
  });

  const edges = data?.books?.edges ?? [];
  const pageInfo = data?.books?.pageInfo;
  const totalCount = data?.books?.totalCount ?? 0;

  const { data: authorsData } = useQuery(GET_AUTHORS, { variables: { limit: 500 }, fetchPolicy: 'cache-and-network' });
  const allAuthors: any[] = authorsData?.authors ?? [];

  const [fetchBook, { data: bookData, loading: bookLoading }] = useLazyQuery(GET_BOOK, {
    fetchPolicy: 'network-only',
    onError: (e) => toast.error(extractGqlError(e)),
  });
  const viewBook = bookData?.book;

  const [createBook, { loading: creating }] = useMutation(CREATE_BOOK, {
    onCompleted: () => { toast.success('Book created'); setShowBookModal(false); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [updateBook, { loading: updating }] = useMutation(UPDATE_BOOK, {
    onCompleted: () => { toast.success('Book updated'); setShowBookModal(false); setEditingBook(null); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [deleteBook, { loading: deleting }] = useMutation(DELETE_BOOK, {
    onCompleted: () => { toast.success('Book deleted'); setDeleteTarget(null); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [addCopy, { loading: addingCopy }] = useMutation(ADD_BOOK_COPY, {
    onCompleted: () => {
      toast.success('Copy added');
      setShowCopyModal(null);
      refetch();
      if (viewBookId) fetchBook({ variables: { id: viewBookId } });
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const bookForm = useForm<BookForm>({
    resolver: zodResolver(bookSchema),
    defaultValues: editingBook
      ? {
          title: editingBook.title,
          subtitle: editingBook.subtitle ?? '',
          isbn13: editingBook.isbn13 ?? '',
          isbn10: editingBook.isbn10 ?? '',
          publisher: editingBook.publisher ?? '',
          language: editingBook.language ?? '',
          pageCount: editingBook.pageCount?.toString() ?? '',
          description: editingBook.description ?? '',
          coverImageUrl: editingBook.coverImageUrl ?? '',
        }
      : {},
  });

  const onBookSubmit = (vals: BookForm) => {
    const input = {
      ...vals,
      pageCount: vals.pageCount ? Number(vals.pageCount) : undefined,
      coverImageUrl: vals.coverImageUrl || undefined,
      authorIds: selectedAuthorIds.length > 0 ? selectedAuthorIds : undefined,
    };
    if (editingBook) {
      updateBook({ variables: { bookId: editingBook.id, input } });
    } else {
      createBook({ variables: { input } });
    }
  };

  const handleEditClick = (book: any) => {
    setEditingBook(book);
    bookForm.reset({
      title: book.title, subtitle: book.subtitle ?? '', isbn13: book.isbn13 ?? '',
      isbn10: book.isbn10 ?? '', publisher: book.publisher ?? '', language: book.language ?? '',
      pageCount: book.pageCount?.toString() ?? '', description: book.description ?? '',
      coverImageUrl: book.coverImageUrl ?? '',
    });
    setSelectedAuthorIds(book.authors?.map((a: any) => a.id) ?? []);
    setShowBookModal(true);
  };

  const handleCreate = () => {
    setEditingBook(null);
    bookForm.reset({ title: '', subtitle: '', isbn13: '', isbn10: '', publisher: '', language: '', pageCount: '', description: '', coverImageUrl: '' });
    setSelectedAuthorIds([]);
    setShowBookModal(true);
  };

  const openView = useCallback((bookId: string) => {
    setViewBookId(bookId);
    setViewTab(0);
    fetchBook({ variables: { id: bookId } });
  }, [fetchBook]);

  const copyForm = useForm<CopyForm>({ resolver: zodResolver(copySchema) });

  const onCopySubmit = (vals: CopyForm) => {
    addCopy({ variables: { input: { bookId: showCopyModal, ...vals } } });
  };

  const copies = viewBook?.copies ?? [];
  const reviews = viewBook?.reviews ?? [];

  const StatMini = ({ icon, value, label, bg }: { icon: React.ReactNode; value: React.ReactNode; label: string; bg: string }) => (
    <div className="flex items-center gap-3 rounded-xl border border-nova-border bg-nova-surface p-4 transition-shadow hover:shadow-md">
      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${bg}`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold text-nova-text">{value}</p>
        <p className="text-xs text-nova-text-muted">{label}</p>
      </div>
    </div>
  );

  const viewTabs = [
    {
      label: 'Details',
      icon: <InformationCircleIcon className="h-4 w-4" />,
      content: bookLoading ? <div className="flex justify-center py-8"><Spinner /></div> : viewBook ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatMini icon={<StarIcon className="h-5 w-5" />} value={viewBook.averageRating ? Number(viewBook.averageRating).toFixed(1) : '—'} label="Avg Rating" bg="bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400" />
            <StatMini icon={<DocumentDuplicateIcon className="h-5 w-5" />} value={<>{viewBook.availableCopies ?? 0}<span className="text-sm font-normal text-nova-text-muted">/{viewBook.totalCopies ?? 0}</span></>} label="Copies Avail" bg="bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400" />
            <StatMini icon={<BookOpenIcon className="h-5 w-5" />} value={viewBook.totalBorrows ?? 0} label="Total Borrows" bg="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400" />
            <StatMini icon={<ChatBubbleLeftRightIcon className="h-5 w-5" />} value={reviews.length} label="Reviews" bg="bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400" />
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <Card className="p-5 space-y-4">
              <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
                <BookOpenIcon className="h-4 w-4" /> Book Information
              </h4>
              <div className="space-y-3 text-sm">
                {([
                  ['Title', viewBook.title],
                  ['Subtitle', viewBook.subtitle || '—'],
                  ['Authors', viewBook.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ') || '—'],
                  ['Categories', viewBook.categories?.map((c: any) => c.name).join(', ') || '—'],
                  ['Publisher', viewBook.publisher || '—'],
                  ['Publication Date', viewBook.publicationDate ? formatDate(viewBook.publicationDate) : '—'],
                  ['Edition', viewBook.edition || '—'],
                  ['Language', viewBook.language || '—'],
                  ['Pages', viewBook.pageCount ?? '—'],
                ] as const).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50 last:border-0">
                    <span className="text-nova-text-muted">{k}</span>
                    <span className="font-medium text-nova-text text-right max-w-[60%] truncate">{v}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card className="p-5 space-y-4">
              <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
                <InformationCircleIcon className="h-4 w-4" /> Identifiers & Metadata
              </h4>
              <div className="space-y-3 text-sm">
                {([
                  ['ISBN-13', viewBook.isbn13 || '—'],
                  ['ISBN-10', viewBook.isbn10 || '—'],
                  ['Rating Count', viewBook.ratingCount ?? 0],
                  ['Added', formatDate(viewBook.createdAt)],
                ] as const).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50 last:border-0">
                    <span className="text-nova-text-muted">{k}</span>
                    <span className="font-mono text-nova-text">{v}</span>
                  </div>
                ))}
              </div>
              {Array.isArray(viewBook.tags) && viewBook.tags.length > 0 && (
                <div className="pt-2">
                  <p className="text-xs text-nova-text-muted mb-2 flex items-center gap-1"><TagIcon className="h-3.5 w-3.5" /> Tags</p>
                  <div className="flex flex-wrap gap-1">
                    {viewBook.tags.map((t: string) => <Badge key={t} variant="neutral" size="xs">{t}</Badge>)}
                  </div>
                </div>
              )}
            </Card>
          </div>
          {viewBook.description && (
            <Card className="p-5">
              <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest mb-3">Description</h4>
              <p className="text-sm text-nova-text leading-relaxed whitespace-pre-line">{viewBook.description}</p>
            </Card>
          )}
        </div>
      ) : null,
    },
    {
      label: 'Copies',
      icon: <DocumentDuplicateIcon className="h-4 w-4" />,
      badge: copies.length || undefined,
      content: bookLoading ? <div className="flex justify-center py-8"><Spinner /></div> : copies.length === 0 ? (
        <EmptyState icon={<DocumentDuplicateIcon />} title="No Copies" description="No physical copies registered." action={
          <Button size="sm" onClick={() => { copyForm.reset({ barcode: '', shelfLocation: '', branch: '', condition: '' }); setShowCopyModal(viewBookId); }}>Add Copy</Button>
        } />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              {['AVAILABLE', 'BORROWED', 'RESERVED', 'MAINTENANCE'].map((st) => {
                const cnt = copies.filter((c: any) => c.status === st).length;
                if (cnt === 0) return null;
                return <Badge key={st} variant={copyStatusColor(st)} size="sm">{st}: {cnt}</Badge>;
              })}
            </div>
            <Button size="sm" variant="outline" leftIcon={<SquaresPlusIcon className="h-4 w-4" />} onClick={() => { copyForm.reset({ barcode: '', shelfLocation: '', branch: '', condition: '' }); setShowCopyModal(viewBookId); }}>Add Copy</Button>
          </div>
          <div className="overflow-x-auto rounded-xl border border-nova-border">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-nova-surface text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                  <th className="px-4 py-3">Barcode</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Condition</th>
                  <th className="px-4 py-3">Location</th>
                  <th className="px-4 py-3">Branch</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nova-border">
                {copies.map((c: any) => (
                  <tr key={c.id} className="hover:bg-nova-surface-hover transition-colors">
                    <td className="px-4 py-3 font-mono text-xs">{c.barcode}</td>
                    <td className="px-4 py-3"><Badge variant={copyStatusColor(c.status)} size="sm">{c.status}</Badge></td>
                    <td className="px-4 py-3"><Badge variant={conditionColor(c.condition)} size="sm">{c.condition ?? '—'}</Badge></td>
                    <td className="px-4 py-3 text-xs text-nova-text-muted">{c.shelfLocation || '—'}</td>
                    <td className="px-4 py-3 text-xs text-nova-text-muted">{c.branch || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ),
    },
    {
      label: 'Reviews',
      icon: <ChatBubbleLeftRightIcon className="h-4 w-4" />,
      badge: reviews.length || undefined,
      content: bookLoading ? <div className="flex justify-center py-8"><Spinner /></div> : reviews.length === 0 ? (
        <EmptyState icon={<ChatBubbleLeftRightIcon />} title="No Reviews" description="No approved reviews for this book yet." />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-5 p-4 rounded-xl bg-nova-surface border border-nova-border">
            <div className="text-center">
              <p className="text-4xl font-black text-nova-text">{viewBook?.averageRating ? Number(viewBook.averageRating).toFixed(1) : '—'}</p>
              <div className="flex items-center gap-0.5 mt-1 justify-center">
                {Array.from({ length: 5 }).map((_, i) => (
                  <StarIcon key={i} className={`h-4 w-4 ${i < Math.round(viewBook?.averageRating ?? 0) ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'}`} />
                ))}
              </div>
              <p className="text-xs text-nova-text-muted mt-1">{reviews.length} review{reviews.length !== 1 ? 's' : ''}</p>
            </div>
            <div className="flex-1 space-y-1">
              {[5, 4, 3, 2, 1].map((star) => {
                const count = reviews.filter((r: any) => (r.rating ?? 0) === star).length;
                const pct = reviews.length > 0 ? (count / reviews.length) * 100 : 0;
                return (
                  <div key={star} className="flex items-center gap-2 text-xs">
                    <span className="text-nova-text-muted w-2">{star}</span>
                    <StarIcon className="h-3 w-3 text-yellow-500" />
                    <div className="flex-1 h-2 rounded-full bg-nova-border overflow-hidden">
                      <div className="h-full rounded-full bg-yellow-500 transition-all" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="text-nova-text-muted w-6 text-right">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
          {reviews.map((r: any) => (
            <Card key={r.id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-medium text-nova-text">{r.user?.firstName} {r.user?.lastName}</p>
                    <span className="text-xs text-nova-text-muted">{formatDate(r.createdAt)}</span>
                  </div>
                  {r.title && <p className="text-sm font-semibold text-nova-text">{r.title}</p>}
                  {r.content && <p className="text-sm text-nova-text-muted mt-1 line-clamp-3">{r.content}</p>}
                </div>
                <div className="flex items-center gap-0.5 shrink-0 ml-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <StarIcon key={i} className={`h-4 w-4 ${i < (r.rating ?? 0) ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'}`} />
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">Books</h1>
          <p className="text-sm text-nova-text-secondary">{totalCount.toLocaleString()} total books</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" leftIcon={<ArrowPathIcon className="h-4 w-4" />} onClick={() => refetch()}>Refresh</Button>
          <Button leftIcon={<PlusCircleIcon className="h-4 w-4" />} onClick={handleCreate}>Add Book</Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="w-64">
          <Input placeholder="Search books…" value={search} onChange={(e) => { setSearch(e.target.value); setAfter(null); }} leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />} />
        </div>
        <div className="w-40">
          <Select value={langFilter} onChange={(v) => { setLangFilter(v); setAfter(null); }} options={langOptions} />
        </div>
      </div>

      {loading && !data ? <LoadingOverlay /> : edges.length === 0 ? (
        <EmptyState icon={<PlusCircleIcon />} title="No books found" description="Add your first book to the catalog." action={<Button onClick={handleCreate} size="sm">Add Book</Button>} />
      ) : (
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-nova-border bg-nova-surface text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">ISBN</th>
                  <th className="px-4 py-3">Language</th>
                  <th className="px-4 py-3">Rating</th>
                  <th className="px-4 py-3">Copies</th>
                  <th className="px-4 py-3">Borrows</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nova-border">
                {edges.filter((e: any) => e?.node).map(({ node: book }: any) => (
                  <tr key={book.id} className="hover:bg-nova-surface-hover transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {book.coverImageUrl ? (
                          <img src={book.coverImageUrl} alt="" className="h-10 w-7 rounded-sm object-cover shadow-sm" />
                        ) : (
                          <div className="flex h-10 w-7 items-center justify-center rounded-sm bg-nova-surface text-[10px] font-bold text-nova-text-muted">?</div>
                        )}
                        <div className="min-w-0">
                          <p className="truncate font-medium text-nova-text">{book.title}</p>
                          <p className="text-xs text-nova-text-muted">
                            {book.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ') || 'Unknown'}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-nova-text-muted">{book.isbn13 || book.isbn10 || '—'}</td>
                    <td className="px-4 py-3"><Badge variant="neutral" size="sm">{book.language ?? '—'}</Badge></td>
                    <td className="px-4 py-3">
                      {book.averageRating ? (
                        <span className="flex items-center gap-1 text-nova-text">
                          <StarIcon className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                          {Number(book.averageRating).toFixed(1)}
                        </span>
                      ) : <span className="text-nova-text-muted">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-nova-text font-medium">{book.availableCopies ?? 0}</span>
                      <span className="text-nova-text-muted">/{book.totalCopies ?? 0}</span>
                    </td>
                    <td className="px-4 py-3 text-nova-text-secondary">{book.totalBorrows ?? 0}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Tooltip content="360° View">
                          <Button variant="ghost" size="sm" onClick={() => openView(book.id)} className="!px-2">
                            <EyeIcon className="h-4 w-4" />
                          </Button>
                        </Tooltip>
                        <Tooltip content="Edit Book">
                          <Button variant="ghost" size="sm" onClick={() => handleEditClick(book)} className="!px-2">
                            <PencilSquareIcon className="h-4 w-4" />
                          </Button>
                        </Tooltip>
                        <Dropdown
                          trigger={<Button variant="ghost" size="sm" className="!px-2"><EllipsisVerticalIcon className="h-4 w-4" /></Button>}
                          items={[
                            { label: 'Add Copy', icon: <SquaresPlusIcon className="h-4 w-4" />, onClick: () => { copyForm.reset({ barcode: '', shelfLocation: '', branch: '', condition: '' }); setShowCopyModal(book.id); } },
                            { label: 'Delete', icon: <TrashIcon className="h-4 w-4" />, onClick: () => setDeleteTarget(book), danger: true },
                          ]}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {pageInfo && <Pagination pageInfo={pageInfo} totalCount={totalCount} currentCount={edges.length} onNext={() => setAfter(pageInfo.endCursor)} />}

      {/* 360° VIEW MODAL */}
      <Modal open={!!viewBookId} onClose={() => setViewBookId(null)} title="" size="full">
        <ModalBody className="!p-0 !space-y-0">
          {viewBook && (
            <div className="relative overflow-hidden bg-gradient-to-r from-emerald-600 via-teal-500 to-cyan-500 px-8 py-6 text-white">
              <div className="absolute inset-0 opacity-10">
                <svg width="100%" height="100%"><defs><pattern id="book-dots" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="currentColor" /></pattern></defs><rect width="100%" height="100%" fill="url(#book-dots)" /></svg>
              </div>
              <div className="relative flex items-center gap-5">
                {viewBook.coverImageUrl ? (
                  <img src={viewBook.coverImageUrl} alt="" className="h-20 w-14 rounded-lg object-cover shadow-lg ring-2 ring-white/20" />
                ) : (
                  <div className="flex h-20 w-14 items-center justify-center rounded-lg bg-white/20 text-white text-2xl font-bold shadow-lg ring-2 ring-white/20">
                    {viewBook.title?.charAt(0)}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h3 className="text-2xl font-bold">{viewBook.title}</h3>
                  <p className="text-white/80 text-sm">{viewBook.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ') || 'Unknown Author'}</p>
                  {viewBook.isbn13 && <p className="text-white/60 text-xs mt-0.5 font-mono">ISBN {viewBook.isbn13}</p>}
                </div>
                <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
                  {viewBook.averageRating ? (
                    <span className="rounded-full bg-white/20 backdrop-blur-sm px-3 py-1 text-xs font-bold flex items-center gap-1">
                      <StarIcon className="h-3.5 w-3.5 fill-yellow-300 text-yellow-300" /> {Number(viewBook.averageRating).toFixed(1)}
                    </span>
                  ) : null}
                  <span className={`rounded-full px-3 py-1 text-xs font-bold ${(viewBook.availableCopies ?? 0) > 0 ? 'bg-green-500/30 text-green-100' : 'bg-red-500/30 text-red-100'}`}>
                    {(viewBook.availableCopies ?? 0) > 0 ? 'Available' : 'Unavailable'}
                  </span>
                  {viewBook.language && <span className="rounded-full bg-white/20 backdrop-blur-sm px-3 py-1 text-xs font-bold">{viewBook.language}</span>}
                </div>
              </div>
            </div>
          )}
          <div className="px-6 py-4">
            <Tabs tabs={viewTabs} active={viewTab} onChange={setViewTab} />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => { if (viewBook) handleEditClick(viewBook); setViewBookId(null); }} leftIcon={<PencilSquareIcon className="h-4 w-4" />}>Edit Book</Button>
          <Button onClick={() => setViewBookId(null)}>Close</Button>
        </ModalFooter>
      </Modal>

      {/* Book Create / Edit Modal */}
      <Modal open={showBookModal} onClose={() => { setShowBookModal(false); setEditingBook(null); }} title={editingBook ? 'Edit Book' : 'Add Book'} size="lg">
        <form onSubmit={bookForm.handleSubmit(onBookSubmit)}>
          <ModalBody>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Title *" {...bookForm.register('title')} error={bookForm.formState.errors.title?.message} />
              <Input label="Subtitle" {...bookForm.register('subtitle')} />
              <Input label="ISBN-13" {...bookForm.register('isbn13')} />
              <Input label="ISBN-10" {...bookForm.register('isbn10')} />
              <Input label="Publisher" {...bookForm.register('publisher')} />
              <Select label="Language" value={bookForm.watch('language') || ''} onChange={(v) => bookForm.setValue('language', v)} options={langOptions} />
              <Input label="Pages" type="number" {...bookForm.register('pageCount')} />
              <Input label="Cover URL" {...bookForm.register('coverImageUrl')} error={bookForm.formState.errors.coverImageUrl?.message} />
            </div>
            {/* Author multi-select */}
            <div className="mt-4">
              <label className="mb-1 block text-sm font-medium text-nova-text">Authors</label>
              <div className="max-h-40 overflow-y-auto rounded-lg border border-nova-border bg-nova-surface p-2 space-y-1">
                {allAuthors.length === 0 ? (
                  <p className="text-xs text-nova-text-muted py-2 text-center">No authors available. Create authors first.</p>
                ) : allAuthors.map((a: any) => (
                  <label key={a.id} className="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-nova-surface-hover cursor-pointer transition-colors">
                    <input
                      type="checkbox"
                      checked={selectedAuthorIds.includes(a.id)}
                      onChange={(e) => {
                        if (e.target.checked) setSelectedAuthorIds((prev) => [...prev, a.id]);
                        else setSelectedAuthorIds((prev) => prev.filter((id) => id !== a.id));
                      }}
                      className="h-4 w-4 rounded border-nova-border text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-nova-text">{a.firstName} {a.lastName}</span>
                    {a.nationality && <span className="text-xs text-nova-text-muted">({a.nationality})</span>}
                  </label>
                ))}
              </div>
              {selectedAuthorIds.length > 0 && (
                <p className="mt-1 text-xs text-nova-text-muted">{selectedAuthorIds.length} author{selectedAuthorIds.length !== 1 ? 's' : ''} selected</p>
              )}
            </div>
            <div className="mt-4">
              <Textarea label="Description" {...bookForm.register('description')} rows={3} />
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => { setShowBookModal(false); setEditingBook(null); }}>Cancel</Button>
            <Button type="submit" isLoading={creating || updating}>{editingBook ? 'Save' : 'Create'}</Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Add Copy Modal */}
      <Modal open={!!showCopyModal} onClose={() => setShowCopyModal(null)} title="Add Book Copy">
        <form onSubmit={copyForm.handleSubmit(onCopySubmit)}>
          <ModalBody>
            <div className="space-y-4">
              <Input label="Barcode *" {...copyForm.register('barcode')} error={copyForm.formState.errors.barcode?.message} />
              <Input label="Shelf Location" {...copyForm.register('shelfLocation')} placeholder="e.g. Floor 2, Shelf B3" />
              <Input label="Branch" {...copyForm.register('branch')} placeholder="Main Campus" />
              <Select label="Condition" value={copyForm.watch('condition') || ''} onChange={(v) => copyForm.setValue('condition', v)} options={[
                { value: '', label: 'Select condition' },
                { value: 'NEW', label: 'New' },
                { value: 'GOOD', label: 'Good' },
                { value: 'FAIR', label: 'Fair' },
                { value: 'POOR', label: 'Poor' },
              ]} />
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setShowCopyModal(null)}>Cancel</Button>
            <Button type="submit" isLoading={addingCopy}>Add Copy</Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      {deleteTarget && (
        <ConfirmDialog
          open
          onClose={() => setDeleteTarget(null)}
          onConfirm={() => deleteBook({ variables: { bookId: deleteTarget.id } })}
          title="Delete Book"
          description={`Are you sure you want to delete "${deleteTarget.title}"? Books with active borrows cannot be deleted.`}
          variant="danger"
          confirmLabel="Delete"
          loading={deleting}
        />
      )}
    </div>
  );
}

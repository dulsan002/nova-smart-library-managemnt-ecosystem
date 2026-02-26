/**
 * AdminAuthorsPage — Full CRUD for managing book authors.
 *
 * Features:
 * - View all authors with search/filter
 * - Create new authors
 * - Edit existing authors
 * - Delete authors (only if no associated books)
 * - 360° panoramic view with gradient banner
 * - Icon-only action buttons
 */

import { useState, useCallback } from 'react';
import { useQuery, useLazyQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  PlusCircleIcon,
  PencilSquareIcon,
  TrashIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
  GlobeAltIcon,
  CalendarDaysIcon,
  BookOpenIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle, useDebounce } from '@/hooks';
import { GET_AUTHORS, GET_AUTHOR } from '@/graphql/queries/catalog';
import { CREATE_AUTHOR, UPDATE_AUTHOR, DELETE_AUTHOR } from '@/graphql/mutations/catalog';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Modal, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { Tooltip } from '@/components/ui/Tooltip';
import { LoadingOverlay, Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Tabs } from '@/components/ui/Tabs';
import { extractGqlError, formatDate } from '@/lib/utils';

const emptyForm = {
  firstName: '', lastName: '', biography: '', birthDate: '', deathDate: '',
  nationality: '', photoUrl: '',
};

export default function AdminAuthorsPage() {
  useDocumentTitle('Manage Authors');

  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 400);

  // Modal states
  const [showFormModal, setShowFormModal] = useState(false);
  const [editingAuthor, setEditingAuthor] = useState<any | null>(null);
  const [viewAuthorId, setViewAuthorId] = useState<string | null>(null);
  const [viewTab, setViewTab] = useState(0);
  const [deleteTarget, setDeleteTarget] = useState<any | null>(null);

  // Form state
  const [form, setForm] = useState(emptyForm);

  /* ─── Queries ─── */
  const { data, loading, refetch } = useQuery(GET_AUTHORS, {
    variables: { search: debouncedSearch || undefined, limit: 200 },
    fetchPolicy: 'cache-and-network',
  });

  const [fetchAuthor, { data: authorData, loading: authorLoading }] = useLazyQuery(GET_AUTHOR, {
    fetchPolicy: 'network-only',
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const authors: any[] = data?.authors ?? [];
  const viewAuthor = authorData?.author;

  /* ─── Mutations ─── */
  const [createAuthor, { loading: creating }] = useMutation(CREATE_AUTHOR, {
    onCompleted: () => { toast.success('Author created'); setShowFormModal(false); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [updateAuthor, { loading: updating }] = useMutation(UPDATE_AUTHOR, {
    onCompleted: () => { toast.success('Author updated'); setShowFormModal(false); setEditingAuthor(null); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [deleteAuthor, { loading: deleting }] = useMutation(DELETE_AUTHOR, {
    onCompleted: () => { toast.success('Author deleted'); setDeleteTarget(null); refetch(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  /* ─── Handlers ─── */
  const handleCreate = () => {
    setEditingAuthor(null);
    setForm(emptyForm);
    setShowFormModal(true);
  };

  const handleEdit = (author: any) => {
    setEditingAuthor(author);
    setForm({
      firstName: author.firstName ?? '',
      lastName: author.lastName ?? '',
      biography: author.biography ?? '',
      birthDate: author.birthDate ?? '',
      deathDate: author.deathDate ?? '',
      nationality: author.nationality ?? '',
      photoUrl: author.photoUrl ?? '',
    });
    setShowFormModal(true);
  };

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!form.firstName || !form.lastName) {
      toast.error('First name and last name are required');
      return;
    }
    const input = {
      firstName: form.firstName,
      lastName: form.lastName,
      biography: form.biography || undefined,
      birthDate: form.birthDate || undefined,
      deathDate: form.deathDate || undefined,
      nationality: form.nationality || undefined,
      photoUrl: form.photoUrl || undefined,
    };
    if (editingAuthor) {
      updateAuthor({ variables: { authorId: editingAuthor.id, input } });
    } else {
      createAuthor({ variables: { input } });
    }
  }, [form, editingAuthor, createAuthor, updateAuthor]);

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteAuthor({ variables: { authorId: deleteTarget.id } });
  };

  const openView = useCallback((authorId: string) => {
    setViewAuthorId(authorId);
    setViewTab(0);
    fetchAuthor({ variables: { id: authorId } });
  }, [fetchAuthor]);

  /* ─── Stats ─── */
  const totalAuthors = authors.length;
  const nationalities = [...new Set(authors.filter((a: any) => a.nationality).map((a: any) => a.nationality))];

  if (loading && authors.length === 0) return <LoadingOverlay />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">Authors</h1>
          <p className="text-sm text-nova-text-secondary">Manage book authors and their profiles</p>
        </div>
        <Button leftIcon={<PlusCircleIcon className="h-4 w-4" />} onClick={handleCreate}>Add Author</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-100 dark:bg-primary-900/30">
              <UserCircleIcon className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <p className="text-lg font-bold text-nova-text">{totalAuthors}</p>
              <p className="text-xs text-nova-text-muted">Total Authors</p>
            </div>
          </div>
        </Card>
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-900/30">
              <GlobeAltIcon className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-lg font-bold text-nova-text">{nationalities.length}</p>
              <p className="text-xs text-nova-text-muted">Nationalities</p>
            </div>
          </div>
        </Card>
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 dark:bg-violet-900/30">
              <BookOpenIcon className="h-5 w-5 text-violet-600" />
            </div>
            <div>
              <p className="text-lg font-bold text-nova-text">{authors.filter((a: any) => a.biography).length}</p>
              <p className="text-xs text-nova-text-muted">With Biographies</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Search */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-nova-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search authors..."
            className="w-full rounded-lg border border-nova-border bg-nova-surface py-2 pl-10 pr-3 text-sm text-nova-text placeholder:text-nova-text-muted"
          />
        </div>
      </div>

      {/* Authors Table */}
      {authors.length === 0 ? (
        <EmptyState
          icon={<UserCircleIcon />}
          title="No authors found"
          description="Add authors to associate them with books."
          action={<Button onClick={handleCreate} size="sm" leftIcon={<PlusCircleIcon className="h-4 w-4" />}>Add Author</Button>}
        />
      ) : (
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-nova-border bg-nova-surface-hover/50">
                  <th className="px-4 py-3 text-left font-medium text-nova-text-secondary">Author</th>
                  <th className="px-4 py-3 text-left font-medium text-nova-text-secondary">Nationality</th>
                  <th className="px-4 py-3 text-left font-medium text-nova-text-secondary">Born</th>
                  <th className="px-4 py-3 text-left font-medium text-nova-text-secondary">Died</th>
                  <th className="px-4 py-3 text-right font-medium text-nova-text-secondary">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nova-border">
                {authors.map((author: any) => (
                  <tr key={author.id} className="hover:bg-nova-surface-hover/30 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {author.photoUrl ? (
                          <img src={author.photoUrl} alt="" className="h-9 w-9 rounded-full object-cover" />
                        ) : (
                          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/30">
                            <span className="text-xs font-bold text-primary-600">
                              {author.firstName?.[0]}{author.lastName?.[0]}
                            </span>
                          </div>
                        )}
                        <div>
                          <p className="font-medium text-nova-text">{author.firstName} {author.lastName}</p>
                          {author.biography && (
                            <p className="text-xs text-nova-text-muted line-clamp-1 max-w-xs">{author.biography}</p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-nova-text-secondary">
                      {author.nationality ? <Badge variant="neutral" size="xs">{author.nationality}</Badge> : '—'}
                    </td>
                    <td className="px-4 py-3 text-nova-text-secondary">
                      {author.birthDate ? formatDate(author.birthDate) : '—'}
                    </td>
                    <td className="px-4 py-3 text-nova-text-secondary">
                      {author.deathDate ? formatDate(author.deathDate) : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <Tooltip content="View Author">
                          <button onClick={() => openView(author.id)} className="rounded-lg p-1.5 text-nova-text-muted hover:bg-nova-surface-hover hover:text-nova-text transition-colors">
                            <EyeIcon className="h-4 w-4" />
                          </button>
                        </Tooltip>
                        <Tooltip content="Edit Author">
                          <button onClick={() => handleEdit(author)} className="rounded-lg p-1.5 text-nova-text-muted hover:bg-nova-surface-hover hover:text-primary-600 transition-colors">
                            <PencilSquareIcon className="h-4 w-4" />
                          </button>
                        </Tooltip>
                        <Tooltip content="Delete Author">
                          <button onClick={() => setDeleteTarget(author)} className="rounded-lg p-1.5 text-nova-text-muted hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 transition-colors">
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </Tooltip>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ─── 360° VIEW MODAL ─── */}
      <Modal open={!!viewAuthorId} onClose={() => setViewAuthorId(null)} title="" size="xl">
        {authorLoading ? (
          <ModalBody><div className="flex justify-center py-12"><Spinner /></div></ModalBody>
        ) : viewAuthor ? (
          <>
            {/* Gradient Banner */}
            <div className="relative -mx-6 -mt-6 mb-6 overflow-hidden rounded-t-xl bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-700 px-8 py-10">
              <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djZoLTZWNDBoNnYtNmgtNlYyOGg2eiIvPjwvZz48L2c+PC9zdmc+')] opacity-30" />
              <div className="relative flex items-center gap-5">
                {viewAuthor.photoUrl ? (
                  <img src={viewAuthor.photoUrl} alt="" className="h-20 w-20 rounded-full border-4 border-white/30 object-cover shadow-xl" />
                ) : (
                  <div className="flex h-20 w-20 items-center justify-center rounded-full border-4 border-white/30 bg-white/20 shadow-xl">
                    <span className="text-2xl font-bold text-white">{viewAuthor.firstName?.[0]}{viewAuthor.lastName?.[0]}</span>
                  </div>
                )}
                <div>
                  <h2 className="text-2xl font-bold text-white">{viewAuthor.firstName} {viewAuthor.lastName}</h2>
                  {viewAuthor.nationality && <p className="text-white/80 text-sm">{viewAuthor.nationality}</p>}
                  <div className="flex gap-2 mt-2">
                    {viewAuthor.birthDate && (
                      <Badge variant="neutral" size="xs">b. {viewAuthor.birthDate}</Badge>
                    )}
                    {viewAuthor.deathDate && (
                      <Badge variant="neutral" size="xs">d. {viewAuthor.deathDate}</Badge>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <Tabs active={viewTab} onChange={setViewTab} tabs={[
              {
                label: 'Profile',
                icon: <UserCircleIcon className="h-4 w-4" />,
                content: (
                  <div className="space-y-6 pt-4">
                    <Card className="p-5 space-y-4">
                      <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
                        <UserCircleIcon className="h-4 w-4" /> Details
                      </h4>
                      <div className="space-y-3 text-sm">
                        {([
                          ['Full Name', `${viewAuthor.firstName} ${viewAuthor.lastName}`],
                          ['Nationality', viewAuthor.nationality || '—'],
                          ['Birth Date', viewAuthor.birthDate ? formatDate(viewAuthor.birthDate) : '—'],
                          ['Death Date', viewAuthor.deathDate ? formatDate(viewAuthor.deathDate) : '—'],
                        ] as const).map(([k, v]) => (
                          <div key={k} className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50 last:border-0">
                            <span className="text-nova-text-muted">{k}</span>
                            <span className="font-medium text-nova-text">{v}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                    {viewAuthor.biography && (
                      <Card className="p-5">
                        <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest mb-3">Biography</h4>
                        <p className="text-sm text-nova-text leading-relaxed whitespace-pre-line">{viewAuthor.biography}</p>
                      </Card>
                    )}
                  </div>
                ),
              },
            ]} />

            <ModalFooter>
              <Button variant="outline" onClick={() => setViewAuthorId(null)}>Close</Button>
              <Button variant="outline" onClick={() => { const id = viewAuthorId; setViewAuthorId(null); if (id) { const a = authors.find((x: any) => x.id === id); if (a) handleEdit(a); } }} leftIcon={<PencilSquareIcon className="h-4 w-4" />}>Edit Author</Button>
            </ModalFooter>
          </>
        ) : null}
      </Modal>

      {/* ─── CREATE / EDIT MODAL ─── */}
      <Modal
        open={showFormModal}
        onClose={() => { setShowFormModal(false); setEditingAuthor(null); setForm(emptyForm); }}
        title={editingAuthor ? 'Edit Author' : 'Add Author'}
        size="xl"
      >
        <form onSubmit={handleSubmit}>
          <ModalBody>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input
                label="First Name *"
                value={form.firstName}
                onChange={(e) => setForm({ ...form, firstName: e.target.value })}
                leftIcon={<UserCircleIcon className="h-4 w-4" />}
              />
              <Input
                label="Last Name *"
                value={form.lastName}
                onChange={(e) => setForm({ ...form, lastName: e.target.value })}
              />
              <Input
                label="Nationality"
                value={form.nationality}
                onChange={(e) => setForm({ ...form, nationality: e.target.value })}
                leftIcon={<GlobeAltIcon className="h-4 w-4" />}
                placeholder="e.g. American"
              />
              <Input
                label="Photo URL"
                value={form.photoUrl}
                onChange={(e) => setForm({ ...form, photoUrl: e.target.value })}
                placeholder="https://..."
              />
              <Input
                label="Birth Date"
                type="date"
                value={form.birthDate}
                onChange={(e) => setForm({ ...form, birthDate: e.target.value })}
                leftIcon={<CalendarDaysIcon className="h-4 w-4" />}
              />
              <Input
                label="Death Date"
                type="date"
                value={form.deathDate}
                onChange={(e) => setForm({ ...form, deathDate: e.target.value })}
                leftIcon={<CalendarDaysIcon className="h-4 w-4" />}
              />
            </div>
            <div className="mt-4">
              <Textarea
                label="Biography"
                value={form.biography}
                onChange={(e) => setForm({ ...form, biography: e.target.value })}
                rows={4}
                placeholder="Brief biography of the author..."
              />
            </div>
          </ModalBody>
          <ModalFooter>
            <Button type="button" variant="outline" onClick={() => { setShowFormModal(false); setEditingAuthor(null); }}>Cancel</Button>
            <Button type="submit" isLoading={creating || updating}>{editingAuthor ? 'Save' : 'Create'}</Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* ─── DELETE CONFIRMATION ─── */}
      {deleteTarget && (
        <ConfirmDialog
          open
          onClose={() => setDeleteTarget(null)}
          onConfirm={handleDelete}
          title="Delete Author"
          description={`Are you sure you want to delete ${deleteTarget.firstName} ${deleteTarget.lastName}? This cannot be undone. Authors with associated books cannot be deleted.`}
          variant="danger"
          confirmLabel="Delete"
          loading={deleting}
        />
      )}
    </div>
  );
}

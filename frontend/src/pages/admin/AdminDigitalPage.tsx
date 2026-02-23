/**
 * AdminDigitalPage — manage digital assets (e-books, audiobooks).
 *
 * Features:
 * - View all uploaded digital assets with book info
 * - Upload new digital assets for existing books
 * - Delete digital assets
 * - Filter by type (E-Book / Audiobook)
 */

import { useState } from 'react';
import { useQuery, useLazyQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  PlusCircleIcon,
  TrashIcon,
  PencilSquareIcon,
  DocumentTextIcon,
  MusicalNoteIcon,
  BookOpenIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { ALL_DIGITAL_ASSETS, GET_DIGITAL_ASSET } from '@/graphql/queries/digital';
import { GET_BOOKS } from '@/graphql/queries/catalog';
import { UPLOAD_DIGITAL_ASSET, DELETE_DIGITAL_ASSET, UPDATE_DIGITAL_ASSET } from '@/graphql/mutations/digital';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { extractGqlError } from '@/lib/utils';

function formatBytes(bytes: number): string {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

function formatDuration(seconds: number): string {
  if (!seconds) return '—';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

type AssetType = '' | 'EBOOK_PDF' | 'EBOOK_EPUB' | 'AUDIOBOOK';

export default function AdminDigitalPage() {
  useDocumentTitle('Manage Digital Content');

  const [typeFilter, setTypeFilter] = useState<AssetType>('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<any | null>(null);
  const [editTarget, setEditTarget] = useState<any | null>(null);
  const [viewAssetId, setViewAssetId] = useState<string | null>(null);

  // Edit form state
  const [editAssetType, setEditAssetType] = useState<'EBOOK_PDF' | 'EBOOK_EPUB' | 'AUDIOBOOK'>('EBOOK_PDF');
  const [editFilePath, setEditFilePath] = useState('');
  const [editFileSize, setEditFileSize] = useState('');
  const [editMimeType, setEditMimeType] = useState('');
  const [editTotalPages, setEditTotalPages] = useState('');
  const [editDuration, setEditDuration] = useState('');
  const [editNarrator, setEditNarrator] = useState('');

  // Upload form state
  const [formBookId, setFormBookId] = useState('');
  const [formAssetType, setFormAssetType] = useState<'EBOOK_PDF' | 'EBOOK_EPUB' | 'AUDIOBOOK'>('EBOOK_PDF');
  const [formFilePath, setFormFilePath] = useState('');
  const [formFileSize, setFormFileSize] = useState('');
  const [formMimeType, setFormMimeType] = useState('');
  const [formTotalPages, setFormTotalPages] = useState('');
  const [formDuration, setFormDuration] = useState('');
  const [formNarrator, setFormNarrator] = useState('');

  const [fetchAsset, { data: assetDetail, loading: assetLoading }] = useLazyQuery(GET_DIGITAL_ASSET, {
    fetchPolicy: 'network-only',
    onError: (e) => toast.error(extractGqlError(e)),
  });
  const viewAsset = assetDetail?.digitalAsset;

  const openAssetView = (id: string) => {
    setViewAssetId(id);
    fetchAsset({ variables: { id } });
  };

  const { data, loading, refetch } = useQuery(ALL_DIGITAL_ASSETS, {
    variables: typeFilter ? { assetType: typeFilter } : {},
    fetchPolicy: 'cache-and-network',
  });

  // Fetch books for the upload dropdown
  const { data: booksData } = useQuery(GET_BOOKS, {
    variables: { first: 100 },
  });

  const assets: any[] = data?.allDigitalAssets ?? [];
  const books: any[] = (booksData?.books?.edges ?? []).map((e: any) => e.node).filter(Boolean);

  const [uploadAsset, { loading: uploading }] = useMutation(UPLOAD_DIGITAL_ASSET, {
    onCompleted: () => {
      toast.success('Digital asset uploaded successfully');
      setShowUploadModal(false);
      resetForm();
      refetch();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const [deleteAsset, { loading: deleting }] = useMutation(DELETE_DIGITAL_ASSET, {
    onCompleted: () => {
      toast.success('Digital asset deleted');
      setDeleteTarget(null);
      refetch();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const [updateAsset, { loading: updatingAsset }] = useMutation(UPDATE_DIGITAL_ASSET, {
    onCompleted: () => {
      toast.success('Digital asset updated');
      setEditTarget(null);
      refetch();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const resetForm = () => {
    setFormBookId('');
    setFormAssetType('EBOOK_PDF');
    setFormFilePath('');
    setFormFileSize('');
    setFormMimeType('');
    setFormTotalPages('');
    setFormDuration('');
    setFormNarrator('');
  };

  const handleUpload = () => {
    if (!formBookId || !formFilePath || !formFileSize) {
      toast.error('Book, file path, and file size are required');
      return;
    }
    uploadAsset({
      variables: {
        bookId: formBookId,
        assetType: formAssetType,
        filePath: formFilePath,
        fileSizeBytes: parseInt(formFileSize, 10) || 0,
        mimeType: formMimeType || undefined,
        totalPages: formTotalPages ? parseInt(formTotalPages, 10) : undefined,
        durationSeconds: formDuration ? parseInt(formDuration, 10) : undefined,
        narrator: formNarrator || undefined,
      },
    });
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteAsset({ variables: { digitalAssetId: deleteTarget.id } });
  };

  const isAudioType = formAssetType === 'AUDIOBOOK';
  const isEditAudio = editAssetType === 'AUDIOBOOK';

  const openEdit = (asset: any) => {
    setEditTarget(asset);
    setEditAssetType(asset.assetType ?? 'EBOOK_PDF');
    setEditFilePath(asset.filePath ?? '');
    setEditFileSize(String(asset.fileSizeBytes ?? ''));
    setEditMimeType(asset.mimeType ?? '');
    setEditTotalPages(asset.totalPages ? String(asset.totalPages) : '');
    setEditDuration(asset.durationSeconds ? String(asset.durationSeconds) : '');
    setEditNarrator(asset.narrator ?? '');
  };

  const handleEditSubmit = () => {
    if (!editTarget) return;
    updateAsset({
      variables: {
        digitalAssetId: editTarget.id,
        assetType: editAssetType,
        filePath: editFilePath || undefined,
        fileSizeBytes: editFileSize ? parseInt(editFileSize, 10) : undefined,
        mimeType: editMimeType || undefined,
        totalPages: editTotalPages ? parseInt(editTotalPages, 10) : undefined,
        durationSeconds: editDuration ? parseInt(editDuration, 10) : undefined,
        narrator: editNarrator || undefined,
      },
    });
  };

  if (loading && assets.length === 0) return <LoadingOverlay />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">Digital Content</h1>
          <p className="text-sm text-nova-text-secondary">
            Manage e-books and audiobooks available to all library members
          </p>
        </div>
        <Button
          leftIcon={<PlusCircleIcon className="h-4 w-4" />}
          onClick={() => setShowUploadModal(true)}
        >
          Upload Asset
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-100 dark:bg-primary-900/30">
              <BookOpenIcon className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <p className="text-lg font-bold text-nova-text">{assets.length}</p>
              <p className="text-xs text-nova-text-muted">Total Assets</p>
            </div>
          </div>
        </Card>
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900/30">
              <DocumentTextIcon className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-lg font-bold text-nova-text">
                {assets.filter((a: any) => a.assetType?.startsWith('EBOOK')).length}
              </p>
              <p className="text-xs text-nova-text-muted">E-Books</p>
            </div>
          </div>
        </Card>
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 dark:bg-violet-900/30">
              <MusicalNoteIcon className="h-5 w-5 text-violet-600" />
            </div>
            <div>
              <p className="text-lg font-bold text-nova-text">
                {assets.filter((a: any) => a.assetType === 'AUDIOBOOK').length}
              </p>
              <p className="text-xs text-nova-text-muted">Audiobooks</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-nova-text-secondary">Filter:</span>
        {(['', 'EBOOK_PDF', 'EBOOK_EPUB', 'AUDIOBOOK'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTypeFilter(t)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              t === typeFilter
                ? 'bg-primary-600 text-white'
                : 'bg-nova-surface-hover text-nova-text-secondary hover:text-nova-text'
            }`}
          >
            {t === '' ? 'All' : t === 'EBOOK_PDF' ? 'PDF E-Book' : t === 'EBOOK_EPUB' ? 'EPUB E-Book' : 'Audiobook'}
          </button>
        ))}
      </div>

      {/* Assets Table */}
      {assets.length === 0 ? (
        <EmptyState
          icon={<BookOpenIcon />}
          title="No digital assets"
          description="Upload e-books and audiobooks for your library members."
          action={
            <Button onClick={() => setShowUploadModal(true)} leftIcon={<PlusCircleIcon className="h-4 w-4" />}>
              Upload First Asset
            </Button>
          }
        />
      ) : (
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-nova-border bg-nova-surface-hover/50">
                  <th className="px-4 py-3 text-left font-medium text-nova-text-secondary">Book</th>
                  <th className="px-4 py-3 text-left font-medium text-nova-text-secondary">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-nova-text-secondary">Details</th>
                  <th className="px-4 py-3 text-left font-medium text-nova-text-secondary">Size</th>
                  <th className="px-4 py-3 text-left font-medium text-nova-text-secondary">Added</th>
                  <th className="px-4 py-3 text-right font-medium text-nova-text-secondary">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nova-border">
                {assets.map((asset: any) => {
                  const isAudio = asset.assetType === 'AUDIOBOOK';
                  return (
                    <tr key={asset.id} className="hover:bg-nova-surface-hover/30 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-8 overflow-hidden rounded bg-gray-100 dark:bg-gray-800 flex-shrink-0">
                            {asset.book?.coverImageUrl ? (
                              <img src={asset.book.coverImageUrl} alt="" className="h-full w-full object-cover" />
                            ) : (
                              <div className="flex h-full items-center justify-center">
                                {isAudio
                                  ? <MusicalNoteIcon className="h-4 w-4 text-gray-300" />
                                  : <DocumentTextIcon className="h-4 w-4 text-gray-300" />}
                              </div>
                            )}
                          </div>
                          <div className="min-w-0">
                            <p className="font-medium text-nova-text line-clamp-1">
                              {asset.book?.title ?? 'Unknown Book'}
                            </p>
                            <p className="text-xs text-nova-text-muted line-clamp-1">
                              {asset.book?.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ')}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={isAudio ? 'info' : 'primary'}
                          size="xs"
                        >
                          {isAudio ? 'Audiobook' : asset.assetType === 'EBOOK_EPUB' ? 'EPUB' : 'PDF'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-nova-text-secondary">
                        {isAudio ? (
                          <span>
                            {formatDuration(asset.durationSeconds)}
                            {asset.narrator && ` · ${asset.narrator}`}
                          </span>
                        ) : (
                          <span>{asset.totalPages ? `${asset.totalPages} pages` : '—'}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-nova-text-secondary">
                        {formatBytes(asset.fileSizeBytes)}
                      </td>
                      <td className="px-4 py-3 text-nova-text-secondary">
                        {asset.createdAt ? new Date(asset.createdAt).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => openAssetView(asset.id)}
                            className="rounded p-1 text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors"
                            title="View details"
                          >
                            <EyeIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => openEdit(asset)}
                            className="rounded p-1 text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
                            title="Edit asset"
                          >
                            <PencilSquareIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => setDeleteTarget(asset)}
                            className="rounded p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                            title="Delete asset"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ─── Upload Modal ─── */}
      <Modal
        open={showUploadModal}
        onClose={() => { setShowUploadModal(false); resetForm(); }}
        title="Upload Digital Asset"
        size="lg"
      >
        <ModalBody>
          <div className="space-y-4">
            {/* Book Select */}
            <div>
              <label className="block text-sm font-medium text-nova-text mb-1">Book *</label>
              <select
                value={formBookId}
                onChange={(e) => setFormBookId(e.target.value)}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
              >
                <option value="">Select a book...</option>
                {books.map((b: any) => (
                  <option key={b.id} value={b.id}>{b.title}</option>
                ))}
              </select>
            </div>

            {/* Asset Type */}
            <div>
              <label className="block text-sm font-medium text-nova-text mb-1">Asset Type *</label>
              <select
                value={formAssetType}
                onChange={(e) => setFormAssetType(e.target.value as any)}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
              >
                <option value="EBOOK_PDF">E-Book (PDF)</option>
                <option value="EBOOK_EPUB">E-Book (EPUB)</option>
                <option value="AUDIOBOOK">Audiobook</option>
              </select>
            </div>

            {/* File Path */}
            <div>
              <label className="block text-sm font-medium text-nova-text mb-1">File Path *</label>
              <input
                type="text"
                value={formFilePath}
                onChange={(e) => setFormFilePath(e.target.value)}
                placeholder="digital/9780132350884/content.pdf"
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
              />
              <p className="text-xs text-nova-text-muted mt-1">Relative path in the storage system</p>
            </div>

            {/* File Size */}
            <div>
              <label className="block text-sm font-medium text-nova-text mb-1">File Size (bytes) *</label>
              <input
                type="number"
                value={formFileSize}
                onChange={(e) => setFormFileSize(e.target.value)}
                placeholder="5000000"
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
              />
            </div>

            {/* MIME Type */}
            <div>
              <label className="block text-sm font-medium text-nova-text mb-1">MIME Type</label>
              <input
                type="text"
                value={formMimeType}
                onChange={(e) => setFormMimeType(e.target.value)}
                placeholder={isAudioType ? 'audio/mpeg' : 'application/pdf'}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
              />
            </div>

            {/* Conditional fields */}
            {isAudioType ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-nova-text mb-1">Duration (seconds)</label>
                  <input
                    type="number"
                    value={formDuration}
                    onChange={(e) => setFormDuration(e.target.value)}
                    placeholder="18000"
                    className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-nova-text mb-1">Narrator</label>
                  <input
                    type="text"
                    value={formNarrator}
                    onChange={(e) => setFormNarrator(e.target.value)}
                    placeholder="Morgan Freeman"
                    className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
                  />
                </div>
              </>
            ) : (
              <div>
                <label className="block text-sm font-medium text-nova-text mb-1">Total Pages</label>
                <input
                  type="number"
                  value={formTotalPages}
                  onChange={(e) => setFormTotalPages(e.target.value)}
                  placeholder="464"
                  className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
                />
              </div>
            )}
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => { setShowUploadModal(false); resetForm(); }}>
            Cancel
          </Button>
          <Button onClick={handleUpload} isLoading={uploading}>
            Upload Asset
          </Button>
        </ModalFooter>
      </Modal>

      {/* ─── Delete Confirmation Modal ─── */}
      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Digital Asset"
        size="sm"
      >
        <ModalBody>
          <p className="text-sm text-nova-text-secondary">
            Are you sure you want to delete the{' '}
            <strong>{deleteTarget?.assetType === 'AUDIOBOOK' ? 'audiobook' : 'e-book'}</strong> for{' '}
            <strong>{deleteTarget?.book?.title}</strong>? This will also remove it from all user libraries.
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setDeleteTarget(null)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete} isLoading={deleting}>
            Delete
          </Button>
        </ModalFooter>
      </Modal>

      {/* ─── Edit Modal ─── */}
      <Modal
        open={!!editTarget}
        onClose={() => setEditTarget(null)}
        title="Edit Digital Asset"
        size="lg"
      >
        <ModalBody>
          <div className="space-y-4">
            {/* Book (read-only) */}
            <div>
              <label className="block text-sm font-medium text-nova-text mb-1">Book</label>
              <input
                type="text"
                value={editTarget?.book?.title ?? ''}
                disabled
                className="w-full rounded-lg border border-nova-border bg-nova-surface-hover px-3 py-2 text-sm text-nova-text-muted cursor-not-allowed"
              />
              <p className="text-xs text-nova-text-muted mt-1">Book cannot be changed after creation</p>
            </div>

            {/* Asset Type */}
            <div>
              <label className="block text-sm font-medium text-nova-text mb-1">Asset Type</label>
              <select
                value={editAssetType}
                onChange={(e) => setEditAssetType(e.target.value as any)}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
              >
                <option value="EBOOK_PDF">E-Book (PDF)</option>
                <option value="EBOOK_EPUB">E-Book (EPUB)</option>
                <option value="AUDIOBOOK">Audiobook</option>
              </select>
            </div>

            {/* File Path */}
            <div>
              <label className="block text-sm font-medium text-nova-text mb-1">File Path</label>
              <input
                type="text"
                value={editFilePath}
                onChange={(e) => setEditFilePath(e.target.value)}
                placeholder="digital/9780132350884/content.pdf"
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
              />
            </div>

            {/* File Size */}
            <div>
              <label className="block text-sm font-medium text-nova-text mb-1">File Size (bytes)</label>
              <input
                type="number"
                value={editFileSize}
                onChange={(e) => setEditFileSize(e.target.value)}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
              />
            </div>

            {/* MIME Type */}
            <div>
              <label className="block text-sm font-medium text-nova-text mb-1">MIME Type</label>
              <input
                type="text"
                value={editMimeType}
                onChange={(e) => setEditMimeType(e.target.value)}
                placeholder={isEditAudio ? 'audio/mpeg' : 'application/pdf'}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
              />
            </div>

            {/* Conditional fields */}
            {isEditAudio ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-nova-text mb-1">Duration (seconds)</label>
                  <input
                    type="number"
                    value={editDuration}
                    onChange={(e) => setEditDuration(e.target.value)}
                    className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-nova-text mb-1">Narrator</label>
                  <input
                    type="text"
                    value={editNarrator}
                    onChange={(e) => setEditNarrator(e.target.value)}
                    className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
                  />
                </div>
              </>
            ) : (
              <div>
                <label className="block text-sm font-medium text-nova-text mb-1">Total Pages</label>
                <input
                  type="number"
                  value={editTotalPages}
                  onChange={(e) => setEditTotalPages(e.target.value)}
                  className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
                />
              </div>
            )}
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setEditTarget(null)}>
            Cancel
          </Button>
          <Button onClick={handleEditSubmit} isLoading={updatingAsset}>
            Save Changes
          </Button>
        </ModalFooter>
      </Modal>

      {/* ─── View Asset Modal ─── */}
      <Modal open={!!viewAssetId} onClose={() => setViewAssetId(null)} title="Digital Asset Details" size="lg">
        <ModalBody>
          {assetLoading ? (
            <div className="flex justify-center py-12"><LoadingOverlay /></div>
          ) : viewAsset ? (
            <div className="space-y-6">
              {/* Book header */}
              <div className="flex items-start gap-4">
                {viewAsset.book?.coverImageUrl ? (
                  <img src={viewAsset.book.coverImageUrl} alt="" className="h-24 w-16 rounded-lg object-cover shadow-md" />
                ) : (
                  <div className="flex h-24 w-16 items-center justify-center rounded-lg bg-nova-surface text-nova-text-muted">
                    {viewAsset.assetType === 'AUDIOBOOK' ? <MusicalNoteIcon className="h-6 w-6" /> : <DocumentTextIcon className="h-6 w-6" />}
                  </div>
                )}
                <div>
                  <h3 className="text-lg font-semibold text-nova-text">{viewAsset.book?.title ?? 'Unknown Book'}</h3>
                  {viewAsset.book?.subtitle && <p className="text-sm text-nova-text-muted">{viewAsset.book.subtitle}</p>}
                  <p className="mt-1 text-sm text-nova-text-secondary">
                    {viewAsset.book?.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ') || 'Unknown Author'}
                  </p>
                </div>
              </div>
              {/* Detail grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-nova-surface-hover/50 p-3">
                  <p className="text-xs font-medium text-nova-text-muted uppercase tracking-wide">Asset Type</p>
                  <p className="mt-1 font-semibold text-nova-text">
                    <Badge variant={viewAsset.assetType === 'AUDIOBOOK' ? 'info' : 'primary'} size="sm">
                      {viewAsset.assetType === 'AUDIOBOOK' ? 'Audiobook' : viewAsset.assetType === 'EBOOK_EPUB' ? 'EPUB' : 'PDF'}
                    </Badge>
                  </p>
                </div>
                <div className="rounded-lg bg-nova-surface-hover/50 p-3">
                  <p className="text-xs font-medium text-nova-text-muted uppercase tracking-wide">MIME Type</p>
                  <p className="mt-1 font-medium text-nova-text">{viewAsset.mimeType || '—'}</p>
                </div>
                <div className="rounded-lg bg-nova-surface-hover/50 p-3">
                  <p className="text-xs font-medium text-nova-text-muted uppercase tracking-wide">File Size</p>
                  <p className="mt-1 font-medium text-nova-text">{formatBytes(viewAsset.fileSizeBytes)}</p>
                </div>
                {viewAsset.assetType === 'AUDIOBOOK' ? (
                  <>
                    <div className="rounded-lg bg-nova-surface-hover/50 p-3">
                      <p className="text-xs font-medium text-nova-text-muted uppercase tracking-wide">Duration</p>
                      <p className="mt-1 font-medium text-nova-text">{formatDuration(viewAsset.durationSeconds)}</p>
                    </div>
                    <div className="rounded-lg bg-nova-surface-hover/50 p-3 col-span-2">
                      <p className="text-xs font-medium text-nova-text-muted uppercase tracking-wide">Narrator</p>
                      <p className="mt-1 font-medium text-nova-text">{viewAsset.narrator || '—'}</p>
                    </div>
                  </>
                ) : (
                  <div className="rounded-lg bg-nova-surface-hover/50 p-3">
                    <p className="text-xs font-medium text-nova-text-muted uppercase tracking-wide">Total Pages</p>
                    <p className="mt-1 font-medium text-nova-text">{viewAsset.totalPages ?? '—'}</p>
                  </div>
                )}
                <div className="rounded-lg bg-nova-surface-hover/50 p-3 col-span-2">
                  <p className="text-xs font-medium text-nova-text-muted uppercase tracking-wide">Added On</p>
                  <p className="mt-1 font-medium text-nova-text">{viewAsset.createdAt ? new Date(viewAsset.createdAt).toLocaleString() : '—'}</p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-center text-nova-text-muted py-8">Asset not found.</p>
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setViewAssetId(null)}>Close</Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}

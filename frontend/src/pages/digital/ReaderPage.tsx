/**
 * ReaderPage — digital content reader with real page rendering,
 * bookmarks, highlights, text selection, and reading-session tracking.
 *
 * Fetches the active session or starts a new one for the given digitalAssetId.
 * Displays content from the digital asset file (proxied via /media/).
 * Keyboard navigation (← →), click-to-bookmark, text-select-to-highlight.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  BookOpenIcon,
  BookmarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowLeftIcon,
  Bars3BottomLeftIcon,
  PaintBrushIcon,
} from '@heroicons/react/24/outline';
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid';
import { useDocumentTitle } from '@/hooks';
import {
  ACTIVE_SESSION,
  MY_LIBRARY,
  MY_BOOKMARKS,
  MY_HIGHLIGHTS,
  GET_DIGITAL_ASSET,
} from '@/graphql/queries/digital';
import {
  START_READING_SESSION,
  END_READING_SESSION,
  UPDATE_READING_PROGRESS,
  ADD_BOOKMARK,
  ADD_HIGHLIGHT,
} from '@/graphql/mutations/digital';
import { Button } from '@/components/ui/Button';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { extractGqlError } from '@/lib/utils';

/* ─── helpers ──────────────────────────────────────── */

function resolveContentUrl(assetId: string, page: number): string {
  // Backend serves paginated content via a REST endpoint proxied through /media/
  return `/media/digital/${assetId}/page/${page}/`;
}

/* ─── component ────────────────────────────────────── */

export default function ReaderPage() {
  const { assetId } = useParams<{ assetId: string }>();
  useDocumentTitle('Reader');

  const [currentPage, setCurrentPage] = useState(1);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showPanel, setShowPanel] = useState(false);
  const [pageContent, setPageContent] = useState<string>('');
  const [contentLoading, setContentLoading] = useState(false);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [positionRestored, setPositionRestored] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const currentPageRef = useRef(1);
  const sessionIdRef = useRef<string | null>(null);
  const totalPagesRef = useRef(0);

  // Keep refs in sync
  useEffect(() => { currentPageRef.current = currentPage; }, [currentPage]);
  useEffect(() => { sessionIdRef.current = sessionId; }, [sessionId]);
  useEffect(() => { totalPagesRef.current = totalPages; }, [totalPages]);

  /* ─── Fetch asset metadata (total pages, book info) ─── */
  const { data: assetData, loading: assetLoading } = useQuery(GET_DIGITAL_ASSET, {
    variables: { id: assetId! },
    skip: !assetId,
  });

  const digitalAsset = assetData?.digitalAsset;
  const book = digitalAsset?.book;

  // Extract totalPages from the digital asset
  useEffect(() => {
    if (digitalAsset?.totalPages) {
      setTotalPages(digitalAsset.totalPages);
    }
  }, [digitalAsset]);

  /* ─── Fetch bookmarks and highlights ─── */
  const { data: bookmarksData, refetch: refetchBookmarks } = useQuery(MY_BOOKMARKS, {
    variables: { digitalAssetId: assetId },
    skip: !assetId,
  });

  const { data: highlightsData, refetch: refetchHighlights } = useQuery(MY_HIGHLIGHTS, {
    variables: { digitalAssetId: assetId },
    skip: !assetId,
  });

  const bookmarks = bookmarksData?.myBookmarks ?? [];
  const highlights = highlightsData?.myHighlights ?? [];
  const isBookmarked = bookmarks.some(
    (b: { position?: string }) => {
      try { return JSON.parse(b.position ?? '{}').page === currentPage; } catch { return false; }
    },
  );

  /* ─── Mutations ─── */
  const [startSession] = useMutation(START_READING_SESSION, {
    onCompleted: (data) => {
      setSessionId(data?.startReadingSession?.id ?? null);
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const [endSession] = useMutation(END_READING_SESSION);

  const [updateProgress] = useMutation(UPDATE_READING_PROGRESS);

  const [addBookmark] = useMutation(ADD_BOOKMARK, {
    onCompleted: () => {
      toast.success('Bookmark added');
      refetchBookmarks();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  const [addHighlight] = useMutation(ADD_HIGHLIGHT, {
    onCompleted: () => {
      toast.success('Highlight saved');
      refetchHighlights();
    },
    onError: (err) => toast.error(extractGqlError(err)),
  });

  /* ─── Fetch user library for position fallback ─── */
  const { data: libData, loading: libLoading } = useQuery(MY_LIBRARY, {
    fetchPolicy: 'cache-and-network',
  });

  const libraryItem = (libData?.myLibrary ?? []).find(
    (item: any) => item.digitalAsset?.id === assetId,
  );

  /* ─── Check for active session on THIS asset ─── */
  const { data: activeSessionData, loading: activeSessionLoading } = useQuery(ACTIVE_SESSION, {
    variables: { digitalAssetId: assetId },
    skip: !assetId,
    fetchPolicy: 'network-only',
  });

  /* ─── Restore position & start/resume session ─── */
  useEffect(() => {
    if (positionRestored) return;
    // Wait for BOTH queries to finish loading before deciding
    if (activeSessionLoading || libLoading) return;

    if (activeSessionData?.activeSession?.id) {
      const session = activeSessionData.activeSession;
      setSessionId(session.id);
      // Restore last reading position from the active session
      if (session.lastPosition) {
        try {
          const raw = session.lastPosition;
          const pos = typeof raw === 'string' ? JSON.parse(raw) : raw;
          if (typeof pos.page === 'number' && pos.page >= 1) setCurrentPage(pos.page);
        } catch { /* use default page */ }
      }
      setPositionRestored(true);
    } else if (assetId && !sessionId) {
      // No active session — restore from library entry if available
      if (libraryItem?.lastPosition) {
        try {
          const pos = typeof libraryItem.lastPosition === 'string'
            ? JSON.parse(libraryItem.lastPosition)
            : libraryItem.lastPosition;
          if (typeof pos.page === 'number' && pos.page >= 1) setCurrentPage(pos.page);
        } catch { /* use default page */ }
      }
      startSession({
        variables: { digitalAssetId: assetId, sessionType: 'READING' },
      });
      setPositionRestored(true);
    }
  }, [activeSessionData, activeSessionLoading, libLoading, assetId, libraryItem, positionRestored]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ─── End session on unmount — save final progress first, then end ─── */
  useEffect(() => {
    return () => {
      const sid = sessionIdRef.current;
      const tp = totalPagesRef.current;
      const cp = currentPageRef.current;
      if (sid && tp > 0) {
        const pct = Math.min((cp / tp) * 100, 100);
        updateProgress({
          variables: {
            sessionId: sid,
            progressPercent: pct,
            position: JSON.stringify({ page: cp }),
          },
        })
          .then(() => endSession({ variables: { sessionId: sid } }))
          .catch(() => endSession({ variables: { sessionId: sid } }).catch(() => {}));
      } else if (sid) {
        endSession({ variables: { sessionId: sid } }).catch(() => {});
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ─── Save progress on visibility change (tab switch) ─── */
  useEffect(() => {
    function handleVisibilityChange() {
      if (document.hidden && sessionIdRef.current && totalPagesRef.current > 0) {
        const pct = (currentPageRef.current / totalPagesRef.current) * 100;
        updateProgress({
          variables: {
            sessionId: sessionIdRef.current,
            progressPercent: Math.min(pct, 100),
            position: JSON.stringify({ page: currentPageRef.current }),
          },
        }).catch(() => {});
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [updateProgress]);

  /* ─── beforeunload — last-resort save via sendBeacon ─── */
  useEffect(() => {
    function handleBeforeUnload() {
      if (sessionIdRef.current && totalPagesRef.current > 0) {
        const pct = (currentPageRef.current / totalPagesRef.current) * 100;
        const payload = JSON.stringify({
          query: `mutation { updateReadingProgress(sessionId: "${sessionIdRef.current}", progressPercent: ${Math.min(pct, 100)}, position: "{\\"page\\": ${currentPageRef.current}}") { id } }`,
        });
        navigator.sendBeacon('/graphql/', new Blob([payload], { type: 'application/json' }));
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  /* ─── Fetch page content from backend ─── */
  const fetchPage = useCallback(
    async (page: number) => {
      if (!assetId) return;
      setContentLoading(true);
      try {
        const res = await fetch(resolveContentUrl(assetId, page));
        if (!res.ok) {
          setPageContent(
            `<p class="text-nova-text-muted italic">Unable to load page ${page}. The server returned status ${res.status}.</p>`,
          );
        } else {
          const contentType = res.headers.get('content-type') ?? '';
          if (contentType.includes('application/json')) {
            const json = await res.json();
            setPageContent(json.html ?? json.text ?? JSON.stringify(json));
          } else {
            setPageContent(await res.text());
          }
        }
      } catch {
        setPageContent(
          `<p class="text-nova-text-muted italic">Network error loading page ${page}. Check your connection.</p>`,
        );
      } finally {
        setContentLoading(false);
      }
    },
    [assetId],
  );

  // Fetch content whenever the page changes
  useEffect(() => {
    fetchPage(currentPage);
  }, [currentPage, fetchPage]);

  /* ─── Save progress on EVERY page turn ─── */
  useEffect(() => {
    if (!sessionId || !totalPages || !positionRestored) return;
    const pct = totalPages > 0 ? (currentPage / totalPages) * 100 : 0;
    updateProgress({
      variables: {
        sessionId,
        progressPercent: Math.min(pct, 100),
        position: JSON.stringify({ page: currentPage }),
      },
    });
  }, [currentPage, sessionId, totalPages, positionRestored]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ─── Also periodically update progress every 30s as heartbeat ─── */
  useEffect(() => {
    if (!sessionId || !totalPages) return;
    const timer = setInterval(() => {
      const pct = totalPages > 0 ? (currentPage / totalPages) * 100 : 0;
      updateProgress({
        variables: {
          sessionId,
          progressPercent: Math.min(pct, 100),
          position: JSON.stringify({ page: currentPage }),
        },
      });
    }, 30_000);
    return () => clearInterval(timer);
  }, [sessionId, currentPage, totalPages, updateProgress]);

  /* ─── Navigation helpers ─── */
  const handlePrevPage = useCallback(() => {
    setCurrentPage((p) => Math.max(1, p - 1));
  }, []);

  const handleNextPage = useCallback(() => {
    setCurrentPage((p) => (totalPages > 0 ? Math.min(totalPages, p + 1) : p + 1));
  }, [totalPages]);

  /* ─── Bookmark current page ─── */
  function handleBookmark() {
    if (!assetId) return;
    addBookmark({
      variables: {
        digitalAssetId: assetId,
        title: `Page ${currentPage}`,
        position: JSON.stringify({ page: currentPage }),
        note: '',
      },
    });
  }

  /* ─── Highlight selected text ─── */
  function handleHighlightSelection() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !assetId) return;
    const text = sel.toString().trim();
    if (!text) return;

    addHighlight({
      variables: {
        digitalAssetId: assetId,
        text,
        positionStart: JSON.stringify({ page: currentPage, offset: sel.anchorOffset }),
        positionEnd: JSON.stringify({ page: currentPage, offset: sel.focusOffset }),
        color: 'yellow',
      },
    });
    sel.removeAllRanges();
  }

  /* ─── Keyboard navigation ─── */
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'ArrowLeft') handlePrevPage();
      if (e.key === 'ArrowRight') handleNextPage();
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [handlePrevPage, handleNextPage]);

  /* ─── Guard: no asset selected ─── */
  if (!assetId) {
    return (
      <EmptyState
        icon={<BookOpenIcon />}
        title="No asset selected"
        action={
          <Link to="/library">
            <Button>Back to Library</Button>
          </Link>
        }
      />
    );
  }

  if (assetLoading) return <LoadingOverlay />;

  const progress = totalPages > 0 ? Math.round((currentPage / totalPages) * 100) : 0;

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col animate-fade-in">
      {/* ─── Reader toolbar ─── */}
      <div className="flex items-center justify-between border-b border-nova-border bg-nova-surface px-4 py-2">
        <div className="flex items-center gap-3">
          <Link to="/library" className="nova-focus rounded-lg p-1.5 text-nova-text-muted hover:text-nova-text">
            <ArrowLeftIcon className="h-5 w-5" />
          </Link>
          <div className="min-w-0">
            <span className="text-sm font-medium text-nova-text truncate block">
              {book?.title ?? 'Reader'}
            </span>
            {book?.authors?.length > 0 && (
              <span className="text-xs text-nova-text-muted truncate block">
                {book.authors.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ')}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-nova-text-muted">
            Page {currentPage}{totalPages > 0 ? ` of ${totalPages}` : ''}
          </span>
          <button
            onClick={handleBookmark}
            className="nova-focus rounded-lg p-1.5 text-nova-text-muted transition-colors hover:text-amber-500"
            title="Bookmark this page"
          >
            {isBookmarked ? (
              <BookmarkSolidIcon className="h-5 w-5 text-amber-500" />
            ) : (
              <BookmarkIcon className="h-5 w-5" />
            )}
          </button>
          <button
            onClick={handleHighlightSelection}
            className="nova-focus rounded-lg p-1.5 text-nova-text-muted transition-colors hover:text-primary-500"
            title="Highlight selected text"
          >
            <PaintBrushIcon className="h-5 w-5" />
          </button>
          <button
            onClick={() => setShowPanel(!showPanel)}
            className="nova-focus rounded-lg p-1.5 text-nova-text-muted transition-colors hover:text-nova-text"
            title="Toggle panel"
          >
            <Bars3BottomLeftIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* ─── Main reading area ─── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Content */}
        <div className="flex-1 overflow-y-auto nova-scrollbar">
          <div className="mx-auto max-w-3xl px-8 py-12">
            {contentLoading ? (
              <div className="flex items-center justify-center min-h-[60vh]">
                <LoadingOverlay />
              </div>
            ) : (
              <div
                ref={contentRef}
                className="nova-prose min-h-[60vh]"
                dangerouslySetInnerHTML={{ __html: pageContent }}
              />
            )}
          </div>
        </div>

        {/* ─── Side panel (bookmarks & highlights) ─── */}
        {showPanel && (
          <div className="w-72 border-l border-nova-border bg-nova-surface p-4 overflow-y-auto nova-scrollbar">
            <h3 className="text-sm font-semibold text-nova-text mb-3">
              Bookmarks ({bookmarks.length})
            </h3>
            {bookmarks.length === 0 ? (
              <p className="text-xs text-nova-text-muted">No bookmarks yet</p>
            ) : (
              <ul className="space-y-2">
                {bookmarks.map((bm: { id: string; position?: string; title?: string; note?: string }) => {
                  let page: number | null = null;
                  try { page = JSON.parse(bm.position ?? '{}').page; } catch { /* ignore */ }
                  return (
                    <li key={bm.id}>
                      <button
                        onClick={() => { if (page) setCurrentPage(page); }}
                        className="w-full rounded-lg p-2 text-left text-sm transition-colors hover:bg-nova-surface-hover"
                      >
                        <span className="font-medium text-nova-text">
                          {bm.title ?? (page ? `Page ${page}` : 'Bookmark')}
                        </span>
                        {bm.note && (
                          <p className="text-xs text-nova-text-muted">{bm.note}</p>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}

            <h3 className="mt-6 text-sm font-semibold text-nova-text mb-3">
              Highlights ({highlights.length})
            </h3>
            {highlights.length === 0 ? (
              <p className="text-xs text-nova-text-muted">No highlights yet. Select text and click the highlight button.</p>
            ) : (
              <ul className="space-y-2">
                {highlights.map((hl: { id: string; text: string; positionStart?: string; note?: string }) => {
                  let page: number | null = null;
                  try { page = JSON.parse(hl.positionStart ?? '{}').page; } catch { /* ignore */ }
                  return (
                    <li
                      key={hl.id}
                      className="cursor-pointer rounded-lg border-l-2 border-amber-400 bg-amber-50/50 p-2 dark:bg-amber-900/10"
                      onClick={() => { if (page) setCurrentPage(page); }}
                    >
                      <p className="text-xs text-nova-text">&ldquo;{hl.text}&rdquo;</p>
                      {hl.note && (
                        <p className="mt-0.5 text-[10px] text-nova-text-muted">{hl.note}</p>
                      )}
                      {page && (
                        <p className="mt-0.5 text-[10px] text-nova-text-muted">Page {page}</p>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}
      </div>

      {/* ─── Bottom navigation ─── */}
      <div className="border-t border-nova-border bg-nova-surface px-4 py-2">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="xs" onClick={handlePrevPage} disabled={currentPage <= 1}>
            <ChevronLeftIcon className="h-4 w-4" />
          </Button>
          <ProgressBar value={progress} size="sm" className="flex-1" />
          <Button
            variant="ghost"
            size="xs"
            onClick={handleNextPage}
            disabled={totalPages > 0 && currentPage >= totalPages}
          >
            <ChevronRightIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

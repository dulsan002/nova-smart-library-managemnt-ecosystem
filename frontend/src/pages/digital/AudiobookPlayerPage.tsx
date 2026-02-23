/**
 * AudiobookPlayerPage — immersive audiobook listening experience.
 *
 * Features:
 * - Simulated playback timer (since backend serves placeholder audio)
 * - Full audio controls (play/pause, seek, skip 15/30 sec)
 * - Playback speed control (0.5x – 3x)
 * - Sleep timer (15, 30, 45, 60, 90 min)
 * - Session tracking (LISTENING type)
 * - Bookmarks for audio positions
 * - Progress bar with duration display
 * - Resume from last position across sessions
 * - Auto-save progress on page leave
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  ArrowLeftIcon,
  BookOpenIcon,
  BookmarkIcon,
  ClockIcon,
  ForwardIcon,
  BackwardIcon,
  SpeakerWaveIcon,
  PauseCircleIcon,
  PlayCircleIcon,
  ListBulletIcon,
} from '@heroicons/react/24/outline';
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid';
import { useDocumentTitle } from '@/hooks';
import { MY_LIBRARY, MY_BOOKMARKS, GET_DIGITAL_ASSET, ACTIVE_SESSION } from '@/graphql/queries/digital';
import {
  START_READING_SESSION,
  END_READING_SESSION,
  UPDATE_READING_PROGRESS,
  ADD_BOOKMARK,
} from '@/graphql/mutations/digital';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { cn, extractGqlError } from '@/lib/utils';

/* ─── helpers ──────────────────────────────── */

function formatTime(seconds: number): string {
  if (!seconds || seconds < 0) return '0:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

const PLAYBACK_SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3];
const SLEEP_OPTIONS = [
  { label: '15 min', value: 15 },
  { label: '30 min', value: 30 },
  { label: '45 min', value: 45 },
  { label: '60 min', value: 60 },
  { label: '90 min', value: 90 },
  { label: 'Off', value: 0 },
];

/* ─── component ────────────────────────────── */

export default function AudiobookPlayerPage() {
  const { assetId } = useParams<{ assetId: string }>();
  useDocumentTitle('Audiobook Player');

  /* ─── state ─── */
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const [showSleepMenu, setShowSleepMenu] = useState(false);
  const [showBookmarks, setShowBookmarks] = useState(false);
  const [sleepTimer, setSleepTimer] = useState(0); // minutes, 0 = off
  const [sleepRemaining, setSleepRemaining] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [positionRestored, setPositionRestored] = useState(false);

  const progressRef = useRef<HTMLDivElement>(null);
  const sleepIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const playbackTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const currentTimeRef = useRef(0);
  const sessionIdRef = useRef<string | null>(null);

  // Keep refs in sync
  useEffect(() => { currentTimeRef.current = currentTime; }, [currentTime]);
  useEffect(() => { sessionIdRef.current = sessionId; }, [sessionId]);

  /* ─── fetch asset metadata ─── */
  const { data: assetData, loading: assetLoading } = useQuery(GET_DIGITAL_ASSET, {
    variables: { id: assetId! },
    skip: !assetId,
  });

  const digitalAsset = assetData?.digitalAsset;
  const book = digitalAsset?.book;
  const totalDuration = digitalAsset?.durationSeconds ?? 0;
  const narrator = digitalAsset?.narrator;

  /* ─── fetch user library entry for last position fallback ─── */
  const { data: libData, loading: libLoading } = useQuery(MY_LIBRARY, {
    fetchPolicy: 'cache-and-network',
  });

  const libraryItem = (libData?.myLibrary ?? []).find(
    (item: any) => item.digitalAsset?.id === assetId,
  );

  /* ─── check for active session on this specific asset ─── */
  const { data: activeSessionData, loading: activeSessionLoading } = useQuery(ACTIVE_SESSION, {
    variables: { digitalAssetId: assetId },
    skip: !assetId,
    fetchPolicy: 'network-only',
  });

  /* ─── bookmarks ─── */
  const { data: bookmarksData, refetch: refetchBookmarks } = useQuery(MY_BOOKMARKS, {
    variables: { digitalAssetId: assetId },
    skip: !assetId,
  });
  const bookmarks = bookmarksData?.myBookmarks ?? [];

  /* ─── mutations ─── */
  const [startSession] = useMutation(START_READING_SESSION, {
    onCompleted: (data) => setSessionId(data?.startReadingSession?.id ?? null),
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

  /* ─── restore position & start/resume session ─── */
  useEffect(() => {
    if (positionRestored) return;
    // Wait for BOTH queries to finish loading before deciding
    if (activeSessionLoading || libLoading) return;

    // Try to restore from active session first
    if (activeSessionData?.activeSession?.id) {
      const session = activeSessionData.activeSession;
      setSessionId(session.id);
      if (session.lastPosition) {
        try {
          const raw = session.lastPosition;
          const pos = typeof raw === 'string' ? JSON.parse(raw) : raw;
          if (typeof pos.time === 'number') setCurrentTime(pos.time);
        } catch { /* use default */ }
      }
      setPositionRestored(true);
      return;
    }

    // No active session — start a new one and restore position from library
    if (assetId && !sessionId) {
      if (libraryItem?.lastPosition) {
        try {
          const pos = typeof libraryItem.lastPosition === 'string'
            ? JSON.parse(libraryItem.lastPosition)
            : libraryItem.lastPosition;
          if (typeof pos.time === 'number') setCurrentTime(pos.time);
        } catch { /* use default */ }
      }
      startSession({
        variables: { digitalAssetId: assetId, sessionType: 'LISTENING' },
      });
      setPositionRestored(true);
    }
  }, [activeSessionData, activeSessionLoading, libLoading, assetId, libraryItem, positionRestored]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ─── end session on unmount — save progress first, then end ─── */
  useEffect(() => {
    return () => {
      const sid = sessionIdRef.current;
      const ct = currentTimeRef.current;
      if (sid && totalDuration > 0) {
        const pct = Math.min((ct / totalDuration) * 100, 100);
        updateProgress({
          variables: {
            sessionId: sid,
            progressPercent: pct,
            position: JSON.stringify({ time: ct }),
          },
        })
          .then(() => endSession({ variables: { sessionId: sid } }))
          .catch(() => endSession({ variables: { sessionId: sid } }).catch(() => {}));
      } else if (sid) {
        endSession({ variables: { sessionId: sid } }).catch(() => {});
      }
    };
  }, [totalDuration]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ─── simulated playback timer ─── */
  useEffect(() => {
    if (playbackTimerRef.current) {
      clearInterval(playbackTimerRef.current);
      playbackTimerRef.current = null;
    }

    if (isPlaying && totalDuration > 0) {
      playbackTimerRef.current = setInterval(() => {
        setCurrentTime((prev) => {
          const next = prev + (playbackSpeed * 0.1);
          if (next >= totalDuration) {
            setIsPlaying(false);
            if (sessionIdRef.current) {
              endSession({ variables: { sessionId: sessionIdRef.current } }).catch(() => {});
            }
            return totalDuration;
          }
          return next;
        });
      }, 100);
    }

    return () => {
      if (playbackTimerRef.current) clearInterval(playbackTimerRef.current);
    };
  }, [isPlaying, playbackSpeed, totalDuration]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ─── update progress every 30s ─── */
  useEffect(() => {
    if (!sessionId || !totalDuration) return;
    const timer = setInterval(() => {
      const pct = totalDuration > 0 ? (currentTimeRef.current / totalDuration) * 100 : 0;
      updateProgress({
        variables: {
          sessionId,
          progressPercent: Math.min(pct, 100),
          position: JSON.stringify({ time: currentTimeRef.current }),
        },
      });
    }, 30_000);
    return () => clearInterval(timer);
  }, [sessionId, totalDuration, updateProgress]);

  /* ─── save progress on visibility change (tab switch / minimize) ─── */
  useEffect(() => {
    function handleVisibilityChange() {
      if (document.hidden && sessionIdRef.current && totalDuration > 0) {
        const pct = (currentTimeRef.current / totalDuration) * 100;
        updateProgress({
          variables: {
            sessionId: sessionIdRef.current,
            progressPercent: Math.min(pct, 100),
            position: JSON.stringify({ time: currentTimeRef.current }),
          },
        }).catch(() => {});
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [totalDuration, updateProgress]);

  /* ─── beforeunload — last-resort save via sendBeacon ─── */
  useEffect(() => {
    function handleBeforeUnload() {
      if (sessionIdRef.current && totalDuration > 0) {
        const pct = (currentTimeRef.current / totalDuration) * 100;
        const payload = JSON.stringify({
          query: `mutation { updateReadingProgress(sessionId: "${sessionIdRef.current}", progressPercent: ${Math.min(pct, 100)}, position: "{\\"time\\": ${currentTimeRef.current}}") { id } }`,
        });
        navigator.sendBeacon('/graphql/', new Blob([payload], { type: 'application/json' }));
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [totalDuration]);

  /* ─── sleep timer logic ─── */
  useEffect(() => {
    if (sleepIntervalRef.current) clearInterval(sleepIntervalRef.current);
    if (sleepTimer <= 0) {
      setSleepRemaining(null);
      return;
    }
    let remaining = sleepTimer * 60;
    setSleepRemaining(remaining);
    sleepIntervalRef.current = setInterval(() => {
      remaining -= 1;
      setSleepRemaining(remaining);
      if (remaining <= 0) {
        if (sleepIntervalRef.current) clearInterval(sleepIntervalRef.current);
        setIsPlaying(false);
        setSleepTimer(0);
        setSleepRemaining(null);
        toast('Sleep timer ended — pausing playback', { icon: '😴' });
      }
    }, 1000);
    return () => {
      if (sleepIntervalRef.current) clearInterval(sleepIntervalRef.current);
    };
  }, [sleepTimer]);

  /* ─── controls ─── */
  const togglePlay = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  const skipForward = useCallback((seconds: number) => {
    setCurrentTime((prev) => Math.min(totalDuration, prev + seconds));
  }, [totalDuration]);

  const skipBackward = useCallback((seconds: number) => {
    setCurrentTime((prev) => Math.max(0, prev - seconds));
  }, []);

  const handleSeek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const bar = progressRef.current;
    if (!bar || !totalDuration) return;
    const rect = bar.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    setCurrentTime(pct * totalDuration);
  }, [totalDuration]);

  const handleAddBookmark = useCallback(() => {
    if (!assetId) return;
    addBookmark({
      variables: {
        digitalAssetId: assetId,
        title: `Bookmark at ${formatTime(currentTime)}`,
        position: JSON.stringify({ time: currentTime }),
        note: '',
      },
    });
  }, [assetId, currentTime, addBookmark]);

  /* ─── keyboard shortcuts ─── */
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      switch (e.key) {
        case ' ':
          e.preventDefault();
          togglePlay();
          break;
        case 'ArrowRight':
          skipForward(15);
          break;
        case 'ArrowLeft':
          skipBackward(15);
          break;
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [togglePlay, skipForward, skipBackward]);

  /* ─── guard ─── */
  if (!assetId) {
    return (
      <EmptyState
        icon={<SpeakerWaveIcon />}
        title="No audiobook selected"
        action={
          <Link to="/library">
            <Button>Back to Library</Button>
          </Link>
        }
      />
    );
  }

  if (assetLoading || libLoading) return <LoadingOverlay />;

  const progress = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0;
  const remaining = totalDuration - currentTime;

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col animate-fade-in bg-gradient-to-b from-nova-surface via-nova-bg to-nova-bg">
      {/* ─── Top bar ─── */}
      <div className="flex items-center justify-between border-b border-nova-border bg-nova-surface/80 backdrop-blur-sm px-4 py-3">
        <Link
          to="/library"
          className="flex items-center gap-2 text-sm text-nova-text-muted hover:text-nova-text transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5" />
          <span>Library</span>
        </Link>
        <div className="flex items-center gap-2">
          {sleepRemaining !== null && (
            <Badge variant="warning" size="xs">
              Sleep: {formatTime(sleepRemaining)}
            </Badge>
          )}
          <Badge variant="primary" size="xs">
            {playbackSpeed}x
          </Badge>
        </div>
      </div>

      {/* ─── Main Content ─── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Player Area */}
        <div className="flex flex-1 flex-col items-center justify-center px-6">
          {/* Cover Art */}
          <div className="relative mb-8">
            <div
              className={cn(
                'h-64 w-64 overflow-hidden rounded-2xl shadow-2xl transition-transform duration-700',
                isPlaying && 'scale-105',
              )}
            >
              {book?.coverImageUrl ? (
                <img
                  src={book.coverImageUrl}
                  alt={book.title}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-primary-600 to-accent-600">
                  <BookOpenIcon className="h-24 w-24 text-white/40" />
                </div>
              )}
            </div>
            {/* Pulsing ring when playing */}
            {isPlaying && (
              <div className="absolute inset-0 -m-2 rounded-2xl border-2 border-primary-400/30 animate-pulse" />
            )}
          </div>

          {/* Book Info */}
          <div className="mb-6 text-center max-w-md">
            <h1 className="text-xl font-bold text-nova-text">
              {book?.title ?? 'Audiobook'}
            </h1>
            <p className="mt-1 text-sm text-nova-text-secondary">
              {book?.authors?.map((a: any) => `${a.firstName} ${a.lastName}`).join(', ')}
            </p>
            {narrator && (
              <p className="mt-0.5 text-xs text-nova-text-muted">
                Narrated by {narrator}
              </p>
            )}
          </div>

          {/* ─── Progress Bar ─── */}
          <div className="w-full max-w-lg mb-6">
            <div
              ref={progressRef}
              onClick={handleSeek}
              className="group relative h-2 cursor-pointer rounded-full bg-gray-200 dark:bg-gray-700"
              role="slider"
              aria-valuenow={currentTime}
              aria-valuemin={0}
              aria-valuemax={totalDuration}
            >
              {/* Buffered track */}
              <div
                className="absolute inset-y-0 left-0 rounded-full bg-primary-600/80 transition-all"
                style={{ width: `${progress}%` }}
              />
              {/* Seek thumb */}
              <div
                className="absolute top-1/2 -translate-y-1/2 h-4 w-4 rounded-full bg-primary-600 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity"
                style={{ left: `calc(${progress}% - 8px)` }}
              />
              {/* Bookmark markers */}
              {bookmarks.map((bm: any) => {
                let time = 0;
                try { time = JSON.parse(bm.position ?? '{}').time ?? 0; } catch { /* ignore */ }
                const pos = totalDuration > 0 ? (time / totalDuration) * 100 : 0;
                return (
                  <div
                    key={bm.id}
                    className="absolute top-0 h-full w-0.5 bg-amber-500"
                    style={{ left: `${pos}%` }}
                    title={bm.title}
                  />
                );
              })}
            </div>
            <div className="mt-1.5 flex justify-between text-xs text-nova-text-muted">
              <span>{formatTime(currentTime)}</span>
              <span>-{formatTime(remaining)}</span>
            </div>
          </div>

          {/* ─── Main Controls ─── */}
          <div className="flex items-center gap-6 mb-6">
            <button
              onClick={() => skipBackward(30)}
              className="text-nova-text-muted hover:text-nova-text transition-colors"
              title="Back 30s"
            >
              <div className="relative">
                <BackwardIcon className="h-7 w-7" />
                <span className="absolute -bottom-3 left-1/2 -translate-x-1/2 text-[9px] font-bold">30</span>
              </div>
            </button>

            <button
              onClick={() => skipBackward(15)}
              className="text-nova-text-secondary hover:text-nova-text transition-colors"
              title="Back 15s"
            >
              <div className="relative">
                <BackwardIcon className="h-8 w-8" />
                <span className="absolute -bottom-3 left-1/2 -translate-x-1/2 text-[9px] font-bold">15</span>
              </div>
            </button>

            <button
              onClick={togglePlay}
              className="text-primary-600 hover:text-primary-700 transition-transform hover:scale-110"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <PauseCircleIcon className="h-16 w-16" />
              ) : (
                <PlayCircleIcon className="h-16 w-16" />
              )}
            </button>

            <button
              onClick={() => skipForward(15)}
              className="text-nova-text-secondary hover:text-nova-text transition-colors"
              title="Forward 15s"
            >
              <div className="relative">
                <ForwardIcon className="h-8 w-8" />
                <span className="absolute -bottom-3 left-1/2 -translate-x-1/2 text-[9px] font-bold">15</span>
              </div>
            </button>

            <button
              onClick={() => skipForward(30)}
              className="text-nova-text-muted hover:text-nova-text transition-colors"
              title="Forward 30s"
            >
              <div className="relative">
                <ForwardIcon className="h-7 w-7" />
                <span className="absolute -bottom-3 left-1/2 -translate-x-1/2 text-[9px] font-bold">30</span>
              </div>
            </button>
          </div>

          {/* ─── Secondary Controls ─── */}
          <div className="flex items-center gap-4">
            {/* Speed */}
            <div className="relative">
              <button
                onClick={() => { setShowSpeedMenu(!showSpeedMenu); setShowSleepMenu(false); }}
                className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold text-nova-text-secondary hover:bg-nova-surface-hover hover:text-nova-text transition-colors"
              >
                {playbackSpeed}x Speed
              </button>
              {showSpeedMenu && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 rounded-xl border border-nova-border bg-nova-surface p-2 shadow-xl z-50">
                  <div className="grid grid-cols-3 gap-1">
                    {PLAYBACK_SPEEDS.map((speed) => (
                      <button
                        key={speed}
                        onClick={() => { setPlaybackSpeed(speed); setShowSpeedMenu(false); }}
                        className={cn(
                          'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                          speed === playbackSpeed
                            ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                            : 'text-nova-text-secondary hover:bg-nova-surface-hover',
                        )}
                      >
                        {speed}x
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="h-5 w-px bg-nova-border" />

            {/* Sleep Timer */}
            <div className="relative">
              <button
                onClick={() => { setShowSleepMenu(!showSleepMenu); setShowSpeedMenu(false); }}
                className={cn(
                  'flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold transition-colors',
                  sleepTimer > 0
                    ? 'text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20'
                    : 'text-nova-text-secondary hover:bg-nova-surface-hover hover:text-nova-text',
                )}
              >
                <ClockIcon className="h-4 w-4" />
                Sleep
              </button>
              {showSleepMenu && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 rounded-xl border border-nova-border bg-nova-surface p-2 shadow-xl z-50">
                  <div className="space-y-0.5">
                    {SLEEP_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => { setSleepTimer(opt.value); setShowSleepMenu(false); }}
                        className={cn(
                          'block w-full rounded-lg px-4 py-1.5 text-left text-xs font-medium transition-colors',
                          opt.value === sleepTimer
                            ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                            : 'text-nova-text-secondary hover:bg-nova-surface-hover',
                        )}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="h-5 w-px bg-nova-border" />

            {/* Bookmark */}
            <button
              onClick={handleAddBookmark}
              className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold text-nova-text-secondary hover:bg-nova-surface-hover hover:text-nova-text transition-colors"
              title="Bookmark current position"
            >
              <BookmarkIcon className="h-4 w-4" />
              Bookmark
            </button>

            {/* Toggle bookmarks panel */}
            <button
              onClick={() => setShowBookmarks(!showBookmarks)}
              className={cn(
                'flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold transition-colors',
                showBookmarks
                  ? 'text-primary-600 bg-primary-50 dark:bg-primary-900/20'
                  : 'text-nova-text-secondary hover:bg-nova-surface-hover hover:text-nova-text',
              )}
            >
              <ListBulletIcon className="h-4 w-4" />
              {bookmarks.length}
            </button>
          </div>
        </div>

        {/* ─── Bookmarks Side Panel ─── */}
        {showBookmarks && (
          <div className="w-72 border-l border-nova-border bg-nova-surface p-4 overflow-y-auto nova-scrollbar">
            <h3 className="mb-3 text-sm font-semibold text-nova-text flex items-center gap-2">
              <BookmarkSolidIcon className="h-4 w-4 text-amber-500" />
              Audio Bookmarks ({bookmarks.length})
            </h3>
            {bookmarks.length === 0 ? (
              <p className="text-xs text-nova-text-muted">
                No bookmarks yet. Click "Bookmark" to save your position.
              </p>
            ) : (
              <ul className="space-y-2">
                {bookmarks.map((bm: any) => {
                  let time = 0;
                  try { time = JSON.parse(bm.position ?? '{}').time ?? 0; } catch { /* ignore */ }
                  return (
                    <li key={bm.id}>
                      <button
                        onClick={() => setCurrentTime(time)}
                        className="w-full rounded-lg border border-nova-border p-3 text-left transition-colors hover:bg-nova-surface-hover"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-nova-text">
                            {bm.title ?? 'Bookmark'}
                          </span>
                          <Badge variant="primary" size="xs">
                            {formatTime(time)}
                          </Badge>
                        </div>
                        {bm.note && (
                          <p className="mt-1 text-xs text-nova-text-muted">{bm.note}</p>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

import { useCallback, useMemo } from 'react';
import api from '../services/baseApi';
import { openSseStream, readSseEvents } from '../services/sseStream';
import { createLogger } from '../utils/logger';

const logger = createLogger('ResumableScan');

const sleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

export interface ScanEvent {
  type: 'started' | 'progress' | 'completed' | 'cancelled' | 'failed' | string;
  data: Record<string, unknown>;
}

// The state shape a `phase`/`searchId`-based feature (username-search, email-search) uses -
// git-recon uses a different `loading`/`error` shape instead (see the module docstring below), so
// this is a common subset, not the only shape `useResumableScan` accepts.
export interface PhaseScanState {
  phase?: string;
  loading?: boolean;
  searchId?: string | number | null;
  error?: string | null;
  [key: string]: unknown;
}

/**
 * The `failed`-event branch every `phase`/`searchId`-shaped feature's `reduce` needs, byte-for-
 * byte identical across them: fall back to the previous `searchId` when the event itself doesn't
 * carry one, so a connection-loss failure (synthesized by this hook, see `reconcileAfterStreamError`
 * below) doesn't clobber an already-known id. Features with a different state shape (git-recon
 * uses `loading`/`error`, not `phase`/`searchId`) write their own `failed` branch instead of using
 * this - forcing every shape through one function would make the function itself as complex as
 * what it replaces.
 */
export function failedReduce<S extends PhaseScanState>(prev: S, event: ScanEvent): S {
  return { ...prev, phase: 'failed', error: event.data.error, searchId: event.data.search_id ?? prev.searchId };
}

/** The `{...initialState, phase: 'running', ...extra}` seed every `startScan` wrapper builds. */
export function buildRunningSeed<S extends object, E extends object>(initialState: S, extra: E): S & E & { phase: 'running' } {
  return { ...initialState, phase: 'running', ...extra };
}

const RECONCILE_POLL_INITIAL_MS = 1000;
const RECONCILE_POLL_MAX_MS = 15000;
const RECONCILE_POLL_BACKOFF_FACTOR = 1.5;
const RECONCILE_POLL_TIMEOUT_MS = 5 * 60 * 1000; // give up waiting after ~5 minutes total

// Keyed by `scopeKey` (one per feature) rather than a single module-level
// variable: this hook is shared across every scan-style feature, so a flat `let` here would let starting one feature's
// scan abort another feature's in-flight one. Module-scoped (not a ref) so a scan
// keeps running - and the abort controller stays reachable to cancel/reset it -
// even after the component that started it unmounts (e.g. the user switches to
// another feature tab and back).
const activeControllers = new Map<string, AbortController>();

// Every scan feature's backend mounts the same routes (backend `core/scans/routes.py`):
// `POST <base>/scan` (SSE), `GET <base>/<runs>/<id>`, `POST <base>/<runs>/<id>/cancel`.
export interface ScanEndpoint {
  base: string;
  runs: 'history' | 'runs';
}

const TERMINAL_STATUSES = ['completed', 'cancelled', 'failed'];

interface ScanTransport {
  startScan: (body: unknown, signal: AbortSignal) => Promise<ReadableStream<Uint8Array>>;
  fetchPersisted: (searchId: string | number) => Promise<{ status: string; [key: string]: unknown }>;
  cancelScan: (searchId: string | number) => Promise<unknown>;
}

function scanTransport({ base, runs }: ScanEndpoint): ScanTransport {
  return {
    startScan(body, signal) {
      return openSseStream(`${base}/scan`, { body, signal });
    },
    async fetchPersisted(searchId) {
      return (await api.get(`${base}/${runs}/${searchId}`)).data;
    },
    async cancelScan(searchId) {
      await api.post(`${base}/${runs}/${searchId}/cancel`);
    },
  };
}

export interface UseResumableScanOptions<S extends PhaseScanState> {
  scopeKey: string;
  state: S;
  setState: (state: S) => void;
  initialState: S;
  endpoint: ScanEndpoint;
  reduce: (prev: S, event: ScanEvent) => S | Promise<S>;
  reconcile: (prev: S, record: { status: string; [key: string]: unknown }) => S | Promise<S>;
}

/**
 * Drives a "start an SSE scan, persist a run server-side, survive a dropped
 * connection" lifecycle shared by every scan-style feature.
 *
 * Callers own their state shape entirely - this hook only threads it through
 * two feature-supplied functions:
 *   - `reduce(prevState, event) => newState | Promise<newState>`: applies one
 *     live SSE event (`{type: 'started'|'progress'|'completed'|'cancelled'|'failed', data: {...}}`)
 *     to state. Awaited sequentially (not run in parallel), since some features
 *     enrich terminal events with an extra API call.
 *   - `reconcile(prevState, persistedRecord) => newState | Promise<newState>`:
 *     applies a persisted run/search record (fetched via REST, shaped differently
 *     than an SSE event) to state, once the stream itself has dropped and polling
 *     finds the run reached a terminal status. Takes `prevState` too (unlike a
 *     plain record-to-state mapper) since the persisted record only carries the
 *     reconciled fields, not ones set once at scan start (e.g. `username`).
 *
 * Both a lost-then-recovered connection (after the reconcile-poll timeout) and
 * an outright failure to even open the stream are folded back through `reduce`
 * with a synthetic `{type: 'failed', data: {error, search_id}}` event, reusing
 * whatever failure-shaping each feature's `reduce` already does for a real SSE
 * 'failed' event - `reduce`'s 'failed' branch should fall back to `prev.searchId`
 * when `event.data.search_id` is absent, so it doesn't clobber an already-known id.
 *
 * The transport (SSE `fetch`, persisted-record poll, cancel request) is owned
 * here, derived from `endpoint` alone - a feature supplies only its `reduce`/
 * `reconcile` and the request body it passes to `startScan`. Not every feature
 * state uses a `phase` field (git-recon's is `loading`/`result`/`error`) - the
 * "is a scan actually running right now" check behind `cancelScan` falls back
 * to `loading` when `phase` isn't present, so it works for both shapes.
 */
export function useResumableScan<S extends PhaseScanState>({
  scopeKey, state, setState, initialState, endpoint, reduce, reconcile,
}: UseResumableScanOptions<S>) {
  const { base, runs } = endpoint;
  const transport = useMemo(() => scanTransport({ base, runs }), [base, runs]);

  const processStream = useCallback(async (
    stream: ReadableStream<Uint8Array>,
    signal: AbortSignal | undefined,
    searchIdRef: { current: string | number | null },
    stateRef: { current: S },
  ) => {
    for await (const raw of readSseEvents(stream, signal)) {
      const event = raw as ScanEvent;
      if (event.type === 'started' && event.data?.search_id != null) {
        searchIdRef.current = event.data.search_id as string | number;
      }
      stateRef.current = await reduce(stateRef.current, event);
      setState(stateRef.current);
    }
  }, [reduce, setState]);

  // The backend scan runs independently of this connection - if the SSE stream
  // itself drops (network hiccup, proxy timeout), the scan may still be running
  // or may have already finished server-side. Poll the persisted record instead
  // of assuming failure, so the UI doesn't show "failed" for a scan that actually
  // succeeded.
  const reconcileAfterStreamError = useCallback(async (searchId: string | number, signal: AbortSignal, seedState: S) => {
    const startedAt = Date.now();
    let delay = RECONCILE_POLL_INITIAL_MS;

    while (Date.now() - startedAt < RECONCILE_POLL_TIMEOUT_MS) {
      if (signal.aborted) return;
      let record;
      try {
        record = await transport.fetchPersisted(searchId);
      } catch (err) {
        logger.error('Failed to reconcile scan state after connection error:', err);
        break;
      }

      if (TERMINAL_STATUSES.includes(record.status)) {
        setState(await reconcile(seedState, record));
        return;
      }

      await sleep(delay);
      delay = Math.min(delay * RECONCILE_POLL_BACKOFF_FACTOR, RECONCILE_POLL_MAX_MS);
    }
    // Gave up waiting - the scan may still genuinely be in progress server-side,
    // but there's no live connection left to keep watching it from here.
    setState(await reduce(seedState, { type: 'failed', data: { error: 'Lost connection to the server', search_id: searchId } }));
  }, [transport, reconcile, reduce, setState]);

  const startScan = useCallback(async (payload: unknown, seedState: S) => {
    const prevController = activeControllers.get(scopeKey);
    if (prevController) prevController.abort();
    const controller = new AbortController();
    activeControllers.set(scopeKey, controller);
    const { signal } = controller;

    const searchIdRef: { current: string | number | null } = { current: null };
    const stateRef: { current: S } = { current: seedState };

    setState(seedState);

    try {
      const stream = await transport.startScan(payload, signal);
      await processStream(stream, signal, searchIdRef, stateRef);
    } catch (err) {
      if (signal.aborted) return;
      logger.error('Scan connection error:', err);
      if (searchIdRef.current != null) {
        await reconcileAfterStreamError(searchIdRef.current, signal, stateRef.current);
      } else {
        const message = err instanceof Error ? err.message : String(err);
        setState(await reduce(stateRef.current, { type: 'failed', data: { error: message } }));
      }
    }
  }, [transport, processStream, reconcileAfterStreamError, reduce, scopeKey, setState]);

  const cancelScan = useCallback(() => {
    const isRunning = state.phase != null ? state.phase === 'running' : Boolean(state.loading);
    if (!isRunning || state.searchId == null) return;
    transport.cancelScan(state.searchId).catch((err: unknown) => logger.error('Cancel request failed:', err));
  }, [transport, state.phase, state.loading, state.searchId]);

  const reset = useCallback(() => {
    const controller = activeControllers.get(scopeKey);
    if (controller) {
      controller.abort();
      activeControllers.delete(scopeKey);
    }
    setState(initialState);
  }, [initialState, scopeKey, setState]);

  return { startScan, cancelScan, reset };
}

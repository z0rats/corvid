import { useCallback } from 'react';
import { createLogger } from '../utils/logger';

const logger = createLogger('ResumableScan');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * The `failed`-event branch every `phase`/`searchId`-shaped feature's `reduce` needs, byte-for-
 * byte identical across them: fall back to the previous `searchId` when the event itself doesn't
 * carry one, so a connection-loss failure (synthesized by this hook, see `reconcileAfterStreamError`
 * below) doesn't clobber an already-known id. Features with a different state shape (git-recon
 * uses `loading`/`error`, not `phase`/`searchId`) write their own `failed` branch instead of using
 * this - forcing every shape through one function would make the function itself as complex as
 * what it replaces.
 */
export function failedReduce(prev, event) {
  return { ...prev, phase: 'failed', error: event.error, searchId: event.search_id ?? prev.searchId };
}

/** The `{...initialState, phase: 'running', ...extra}` seed every `startScan` wrapper builds. */
export function buildRunningSeed(initialState, extra) {
  return { ...initialState, phase: 'running', ...extra };
}

const RECONCILE_POLL_INITIAL_MS = 1000;
const RECONCILE_POLL_MAX_MS = 15000;
const RECONCILE_POLL_BACKOFF_FACTOR = 1.5;
const RECONCILE_POLL_TIMEOUT_MS = 5 * 60 * 1000; // give up waiting after ~5 minutes total

// Keyed by `scopeKey` (one per feature) rather than a single module-level
// variable: this hook is shared across every scan-style feature (username-search,
// email-search, git-recon), so a flat `let` here would let starting one feature's
// scan abort another feature's in-flight one. Module-scoped (not a ref) so a scan
// keeps running - and the abort controller stays reachable to cancel/reset it -
// even after the component that started it unmounts (e.g. the user switches to
// another feature tab and back).
const activeControllers = new Map();

/**
 * Drives a "start an SSE scan, persist a run server-side, survive a dropped
 * connection" lifecycle shared by every scan-style feature.
 *
 * Callers own their state shape entirely - this hook only threads it through
 * two feature-supplied functions:
 *   - `reduce(prevState, event) => newState | Promise<newState>`: applies one
 *     live SSE event (`{type: 'started'|'progress'|'completed'|'cancelled'|'failed', ...}`)
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
 * with a synthetic `{type: 'failed', error, search_id}` event, reusing whatever
 * failure-shaping each feature's `reduce` already does for a real SSE 'failed'
 * event - `reduce`'s 'failed' branch should fall back to `prev.searchId` when
 * `event.search_id` is absent, so it doesn't clobber an already-known id.
 *
 * `cancelScan` is only exposed when `api.cancelScan` is provided, and assumes
 * cancel-capable feature state has `phase`/`searchId` fields (true for both
 * current cancel-capable features - the one feature without cancel, git-recon,
 * doesn't use `phase` either).
 */
export function useResumableScan({ scopeKey, state, setState, initialState, terminalStatuses, api, reduce, reconcile }) {
  const processStream = useCallback(async (stream, signal, searchIdRef, stateRef) => {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        if (signal?.aborted) break;
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop();

        for (const chunk of chunks) {
          if (!chunk.startsWith('data: ')) continue;

          let event;
          try {
            event = JSON.parse(chunk.substring(6));
          } catch (err) {
            logger.error('Failed to parse SSE event:', err, chunk);
            continue;
          }

          if (event.type === 'started' && event.search_id != null) {
            searchIdRef.current = event.search_id;
          }

          stateRef.current = await reduce(stateRef.current, event);
          setState(stateRef.current);
        }
      }
    } finally {
      reader.releaseLock();
    }
  }, [reduce, setState]);

  // The backend scan runs independently of this connection - if the SSE stream
  // itself drops (network hiccup, proxy timeout), the scan may still be running
  // or may have already finished server-side. Poll the persisted record instead
  // of assuming failure, so the UI doesn't show "failed" for a scan that actually
  // succeeded.
  const reconcileAfterStreamError = useCallback(async (searchId, signal, seedState) => {
    const startedAt = Date.now();
    let delay = RECONCILE_POLL_INITIAL_MS;

    while (Date.now() - startedAt < RECONCILE_POLL_TIMEOUT_MS) {
      if (signal.aborted) return;
      let record;
      try {
        record = await api.fetchPersisted(searchId);
      } catch (err) {
        logger.error('Failed to reconcile scan state after connection error:', err);
        break;
      }

      if (terminalStatuses.includes(record.status)) {
        setState(await reconcile(seedState, record));
        return;
      }

      await sleep(delay);
      delay = Math.min(delay * RECONCILE_POLL_BACKOFF_FACTOR, RECONCILE_POLL_MAX_MS);
    }
    // Gave up waiting - the scan may still genuinely be in progress server-side,
    // but there's no live connection left to keep watching it from here.
    setState(await reduce(seedState, { type: 'failed', error: 'Lost connection to the server', search_id: searchId }));
  }, [api, reconcile, reduce, setState, terminalStatuses]);

  const startScan = useCallback(async (payload, seedState) => {
    const prevController = activeControllers.get(scopeKey);
    if (prevController) prevController.abort();
    const controller = new AbortController();
    activeControllers.set(scopeKey, controller);
    const { signal } = controller;

    const searchIdRef = { current: null };
    const stateRef = { current: seedState };

    setState(seedState);

    try {
      const stream = await api.startScan(payload, { signal });
      await processStream(stream, signal, searchIdRef, stateRef);
    } catch (err) {
      if (signal.aborted) return;
      logger.error('Scan connection error:', err);
      if (searchIdRef.current != null) {
        await reconcileAfterStreamError(searchIdRef.current, signal, stateRef.current);
      } else {
        setState(await reduce(stateRef.current, { type: 'failed', error: err.message }));
      }
    }
  }, [api, processStream, reconcileAfterStreamError, reduce, scopeKey, setState]);

  // useCallback must run unconditionally (Rules of Hooks) - the capability gate
  // (only expose cancelScan when api.cancelScan exists) happens on the return
  // value below, not on whether this hook call happens at all.
  const cancelScanCallback = useCallback(() => {
    if (!api.cancelScan) return;
    if (state.phase !== 'running' || state.searchId == null) return;
    api.cancelScan(state.searchId).catch((err) => logger.error('Cancel request failed:', err));
  }, [api, state.phase, state.searchId]);
  const cancelScan = api.cancelScan ? cancelScanCallback : undefined;

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

import { act, renderHook } from '@testing-library/react';
import { useState } from 'react';
import baseApi from '../services/baseApi';
import { failedReduce, buildRunningSeed, useResumableScan } from './useResumableScan';

vi.mock('../services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn() },
  baseURL: 'http://backend.test',
}));
vi.mock('../utils/accessToken', () => ({ getAccessToken: () => 'tok' }));

describe('failedReduce', () => {
  it('sets phase to failed and carries the event error', () => {
    const prev = { phase: 'running', searchId: 'abc', checked: 3 };
    expect(failedReduce(prev, { data: { error: 'boom', search_id: 'abc' } })).toEqual({
      phase: 'failed', searchId: 'abc', checked: 3, error: 'boom',
    });
  });

  it('falls back to the previous searchId when the event carries none', () => {
    const prev = { phase: 'running', searchId: 'abc' };
    expect(failedReduce(prev, { data: { error: 'lost connection' } }).searchId).toBe('abc');
  });
});

describe('buildRunningSeed', () => {
  it('merges initialState, phase: running, and the extra fields', () => {
    expect(buildRunningSeed({ phase: 'idle', foundSites: [] }, { username: 'alice' })).toEqual({
      phase: 'running', foundSites: [], username: 'alice',
    });
  });

  it('lets extra fields override initialState', () => {
    expect(buildRunningSeed({ phase: 'idle', username: '' }, { username: 'bob' }).username).toBe('bob');
  });
});

// The tests below drive `useResumableScan` itself through its real interface
// (startScan/cancelScan/reset) against a faked network - `fetch` for the SSE
// stream, `baseApi` for the persisted-record poll and the cancel request -
// rather than through one feature's hook: this is the shared module every scan
// feature depends on, so its transport/reconnect/abort/cancel-gate logic is
// tested once here instead of being re-proven per feature. Each scenario
// describes the backend as `{ startScan, fetchPersisted, cancelScan }`;
// `installBackend` routes the real requests to it.

function encodeSseFrames(events) {
  return events.map((event) => `data: ${JSON.stringify(event)}\n\n`);
}

// `pull` is only invoked once the previously enqueued chunk has been read, so
// this mirrors a real network stream delivering one SSE frame per read.
function makeSseStream(frames, { errorAfter = false } = {}) {
  const encoder = new TextEncoder();
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < frames.length) {
        controller.enqueue(encoder.encode(frames[i]));
        i += 1;
        return;
      }
      if (errorAfter) {
        controller.error(new Error('stream broke'));
        return;
      }
      controller.close();
    },
  });
}

// A stream whose reads never resolve - stands in for an in-flight fetch/SSE
// connection that's still open when something else (a new scan, `reset()`)
// needs to interrupt it.
function makeBlockingStream() {
  return new ReadableStream({ pull() {} });
}

const genericReduce = (prev, event) => {
  if (event.type === 'started') return { ...prev, phase: 'running', searchId: event.data.search_id };
  if (event.type === 'progress') return { ...prev, checked: event.data.checked };
  if (event.type === 'completed') return { ...prev, phase: 'completed' };
  if (event.type === 'failed') return failedReduce(prev, event);
  return prev;
};

const genericReconcile = (prev, record) => ({ ...prev, phase: record.status, result: record.result ?? null });

const baseInitialState = { phase: 'idle', searchId: null, checked: 0 };

// Defensive: if a fake-timer test times out before reaching its own
// `vi.useRealTimers()`, leaving fake timers active would hang every
// subsequent test's `act()` (React's scheduler relies on real timers too).
afterEach(() => vi.useRealTimers());

const ENDPOINT = { base: '/api/test', runs: 'history' };

function installBackend(api) {
  vi.stubGlobal('fetch', vi.fn(async (url, init) => {
    const body = await api.startScan(JSON.parse(init.body), { signal: init.signal, url, init });
    return { ok: true, body };
  }));
  baseApi.get.mockImplementation(async (url) => ({
    data: await api.fetchPersisted(Number(url.split('/').pop())),
  }));
  baseApi.post.mockImplementation(async (url) => {
    await api.cancelScan?.(Number(url.split('/').at(-2)));
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

function useHarness({
  api, reduce = genericReduce, reconcile = genericReconcile, initialState = baseInitialState, scopeKey,
}) {
  useState(() => installBackend(api)); // once per mount, not per render
  const [state, setState] = useState(initialState);
  const scan = useResumableScan({
    scopeKey, state, setState, initialState, endpoint: ENDPOINT, reduce, reconcile,
  });
  return { state, ...scan };
}

describe('useResumableScan — transport', () => {
  it('POSTs the body to <base>/scan as an authenticated SSE request', async () => {
    const api = { startScan: vi.fn().mockResolvedValue(makeSseStream([])), fetchPersisted: vi.fn() };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'transport-1' }));

    await act(async () => {
      await result.current.startScan({ domain: 'example.com' }, buildRunningSeed(baseInitialState, {}));
    });

    const [url, init] = fetch.mock.calls[0];
    expect(url).toBe('http://backend.test/api/test/scan');
    expect(init.method).toBe('POST');
    expect(init.headers).toMatchObject({ Accept: 'text/event-stream', Authorization: 'Bearer tok' });
    expect(JSON.parse(init.body)).toEqual({ domain: 'example.com' });
  });

  it('turns a non-OK response into a failed event', async () => {
    const { result } = renderHook(() => useHarness({ api: { startScan: vi.fn(), fetchPersisted: vi.fn() }, scopeKey: 'transport-2' }));
    fetch.mockResolvedValueOnce({ ok: false, statusText: 'Forbidden', body: null });

    await act(async () => {
      await result.current.startScan({}, buildRunningSeed(baseInitialState, {}));
    });

    expect(result.current.state).toMatchObject({ phase: 'failed', error: 'Server error: Forbidden' });
  });

  it('polls <base>/<runs>/<id> and cancels via <base>/<runs>/<id>/cancel', () => {
    const { result } = renderHook(() => useHarness({
      api: { startScan: vi.fn(), fetchPersisted: vi.fn(), cancelScan: vi.fn() },
      scopeKey: 'transport-3',
      initialState: { phase: 'running', searchId: 42 },
    }));

    act(() => { result.current.cancelScan(); });

    expect(baseApi.post).toHaveBeenCalledWith('/api/test/history/42/cancel');
  });
});

describe('useResumableScan — processStream', () => {
  it('applies SSE events sequentially through reduce and tracks the search id', async () => {
    const frames = encodeSseFrames([
      { type: 'started', data: { search_id: 7 } },
      { type: 'progress', data: { checked: 3 } },
      { type: 'completed', data: {} },
    ]);
    const api = { startScan: vi.fn().mockResolvedValue(makeSseStream(frames)), fetchPersisted: vi.fn() };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'process-stream-1' }));

    await act(async () => {
      await result.current.startScan({}, buildRunningSeed(baseInitialState, {}));
    });

    expect(result.current.state).toEqual({ phase: 'completed', searchId: 7, checked: 3 });
  });

  it('skips chunks that are not SSE data frames or fail to parse, without breaking the loop', async () => {
    const frames = [
      'not-a-data-frame\n\n',
      'data: {not valid json\n\n',
      ...encodeSseFrames([{ type: 'started', data: { search_id: 1 } }]),
    ];
    const api = { startScan: vi.fn().mockResolvedValue(makeSseStream(frames)), fetchPersisted: vi.fn() };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'process-stream-2' }));

    await act(async () => {
      await result.current.startScan({}, buildRunningSeed(baseInitialState, {}));
    });

    expect(result.current.state.searchId).toBe(1);
  });
});

describe('useResumableScan — reconnection after a dropped stream', () => {
  it('reconciles via the persisted record once fetchPersisted reports a terminal status', async () => {
    const frames = encodeSseFrames([{ type: 'started', data: { search_id: 9 } }]);
    const api = {
      startScan: vi.fn().mockResolvedValue(makeSseStream(frames, { errorAfter: true })),
      fetchPersisted: vi.fn().mockResolvedValue({ status: 'completed', result: 'ok' }),
    };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'reconnect-1' }));

    await act(async () => {
      await result.current.startScan({}, buildRunningSeed(baseInitialState, {}));
    });

    expect(api.fetchPersisted).toHaveBeenCalledWith(9);
    expect(result.current.state).toMatchObject({ phase: 'completed', result: 'ok' });
  });

  it('polls with backoff until a terminal status appears', async () => {
    vi.useFakeTimers();
    try {
      const frames = encodeSseFrames([{ type: 'started', data: { search_id: 9 } }]);
      const api = {
        startScan: vi.fn().mockResolvedValue(makeSseStream(frames, { errorAfter: true })),
        fetchPersisted: vi.fn()
          .mockResolvedValueOnce({ status: 'running' })
          .mockResolvedValueOnce({ status: 'running' })
          .mockResolvedValueOnce({ status: 'completed', result: 'ok' }),
      };
      const { result } = renderHook(() => useHarness({ api, scopeKey: 'reconnect-2' }));

      let scanPromise;
      act(() => {
        scanPromise = result.current.startScan({}, buildRunningSeed(baseInitialState, {}));
      });

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1000); // initial poll delay
        await vi.advanceTimersByTimeAsync(1500); // backoff x1.5
        await scanPromise;
      });

      expect(api.fetchPersisted).toHaveBeenCalledTimes(3);
      expect(result.current.state.phase).toBe('completed');
    } finally {
      vi.useRealTimers();
    }
  });

  it('falls back to a synthetic failed event once the reconcile timeout is exceeded', async () => {
    vi.useFakeTimers();
    const frames = encodeSseFrames([{ type: 'started', data: { search_id: 9 } }]);
    const api = {
      startScan: vi.fn().mockResolvedValue(makeSseStream(frames, { errorAfter: true })),
      fetchPersisted: vi.fn().mockResolvedValue({ status: 'running' }),
    };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'reconnect-3' }));

    let scanPromise;
    act(() => {
      scanPromise = result.current.startScan({}, buildRunningSeed(baseInitialState, {}));
    });

    await act(async () => {
      // Advance in bounded steps rather than one huge jump - past
      // RECONCILE_POLL_TIMEOUT_MS (5 minutes) once the backoff-capped
      // 15s-per-poll delay is accounted for.
      for (let i = 0; i < 25; i += 1) {
        await vi.advanceTimersByTimeAsync(15000);
      }
      await scanPromise;
    });

    expect(result.current.state.phase).toBe('failed');
    expect(result.current.state.error).toBe('Lost connection to the server');
    vi.useRealTimers();
  }, 15000);

  it('applies a failed event via reduce when the stream never opens, without polling for reconciliation', async () => {
    const api = { startScan: vi.fn().mockRejectedValue(new Error('network down')), fetchPersisted: vi.fn() };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'reconnect-4' }));

    await act(async () => {
      await result.current.startScan({}, buildRunningSeed(baseInitialState, {}));
    });

    expect(api.fetchPersisted).not.toHaveBeenCalled();
    expect(result.current.state).toMatchObject({ phase: 'failed', error: 'network down' });
  });
});

describe('useResumableScan — per-scopeKey abort', () => {
  it('aborts the in-flight scan under the same scopeKey when a new one starts', async () => {
    let capturedSignal;
    const api1 = {
      startScan: vi.fn((payload, { signal }) => {
        capturedSignal = signal;
        return Promise.resolve(makeBlockingStream());
      }),
      fetchPersisted: vi.fn(),
    };
    const hook1 = renderHook(() => useHarness({ api: api1, scopeKey: 'shared-scope' }));

    act(() => {
      hook1.result.current.startScan({}, buildRunningSeed(baseInitialState, {}));
    });
    await act(async () => {
      await Promise.resolve();
    });
    expect(capturedSignal.aborted).toBe(false);

    const api2 = {
      startScan: vi.fn().mockResolvedValue(makeSseStream(encodeSseFrames([{ type: 'started', data: { search_id: 5 } }]))),
      fetchPersisted: vi.fn(),
    };
    const hook2 = renderHook(() => useHarness({ api: api2, scopeKey: 'shared-scope' }));

    await act(async () => {
      await hook2.result.current.startScan({}, buildRunningSeed(baseInitialState, {}));
    });

    expect(capturedSignal.aborted).toBe(true);
    expect(hook2.result.current.state.searchId).toBe(5);
  });
});

describe('useResumableScan — cancelScan gate', () => {
  it('calls api.cancelScan with the running searchId when phase is "running"', () => {
    const api = { startScan: vi.fn(), fetchPersisted: vi.fn(), cancelScan: vi.fn().mockResolvedValue(undefined) };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'gate-phase', initialState: { phase: 'running', searchId: 42 } }));

    act(() => { result.current.cancelScan(); });

    expect(api.cancelScan).toHaveBeenCalledWith(42);
  });

  it('falls back to the loading flag when state has no phase field (git-recon/ru-business-check shape)', () => {
    const api = { startScan: vi.fn(), fetchPersisted: vi.fn(), cancelScan: vi.fn().mockResolvedValue(undefined) };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'gate-loading', initialState: { loading: true, searchId: 7 } }));

    act(() => { result.current.cancelScan(); });

    expect(api.cancelScan).toHaveBeenCalledWith(7);
  });

  it('does not call the api when no scan is running', () => {
    const api = { startScan: vi.fn(), fetchPersisted: vi.fn(), cancelScan: vi.fn() };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'gate-idle', initialState: { phase: 'idle', searchId: null } }));

    act(() => { result.current.cancelScan(); });

    expect(api.cancelScan).not.toHaveBeenCalled();
  });

  it('does not call the api once the scan has already finished', () => {
    const api = { startScan: vi.fn(), fetchPersisted: vi.fn(), cancelScan: vi.fn() };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'gate-finished', initialState: { phase: 'completed', searchId: 42 } }));

    act(() => { result.current.cancelScan(); });

    expect(api.cancelScan).not.toHaveBeenCalled();
  });
});

describe('useResumableScan — reset', () => {
  it('aborts any in-flight scan and restores initialState', async () => {
    let capturedSignal;
    const api = {
      startScan: vi.fn((payload, { signal }) => {
        capturedSignal = signal;
        return Promise.resolve(makeBlockingStream());
      }),
      fetchPersisted: vi.fn(),
    };
    const { result } = renderHook(() => useHarness({ api, scopeKey: 'reset-scope' }));

    act(() => {
      result.current.startScan({}, buildRunningSeed(baseInitialState, {}));
    });
    await act(async () => {
      await Promise.resolve();
    });

    act(() => { result.current.reset(); });

    expect(capturedSignal.aborted).toBe(true);
    expect(result.current.state).toEqual(baseInitialState);
  });
});

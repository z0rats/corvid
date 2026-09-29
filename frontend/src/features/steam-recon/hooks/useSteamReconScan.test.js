import { reduce, reconcile } from './useSteamReconScan';
import { steamReconApi } from '../services/api/steamReconApi';
import { SCAN_INITIAL_STATE } from '../state/steamReconAtoms';

// This hook plugs its own `reduce`/`reconcile` into the shared `useResumableScan` (see
// core/hooks/useResumableScan.test.js for the reconnect/abort/cancel-gate mechanics that hook
// owns) - these tests only cover what's specific to steam-recon: how one SSE event or one
// persisted search record maps onto this feature's state shape.

vi.mock('../services/api/steamReconApi', () => ({ steamReconApi: { getSearch: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('useSteamReconScan reduce', () => {
  const running = { ...SCAN_INITIAL_STATE, phase: 'running', target: 'robinwalker' };

  it('captures the searchId on "started"', async () => {
    const next = await reduce(running, { type: 'started', data: { search_id: 9 } });
    expect(next).toMatchObject({ searchId: 9 });
  });

  it('tracks the current stage and counters on "progress"', async () => {
    const next = await reduce(running, {
      type: 'progress',
      data: { stage: 'mutual', analyzed: 3, candidates_selected: 10 },
    });
    expect(next).toMatchObject({ stage: 'mutual', analyzed: 3, candidatesSelected: 10, friendsTotal: 0 });
  });

  it('leaves untouched progress fields alone when a progress event omits them', async () => {
    const prev = { ...running, friendsTotal: 40, analyzed: 5 };
    const next = await reduce(prev, { type: 'progress', data: { stage: 'scoring' } });
    expect(next).toMatchObject({ stage: 'scoring', friendsTotal: 40, analyzed: 5 });
  });

  it('fetches the persisted record and stores it as `result` on "completed"', async () => {
    const persisted = { id: 9, status: 'completed', result: { profile: { steamid64: '1' } } };
    steamReconApi.getSearch.mockResolvedValue(persisted);

    const next = await reduce(running, { type: 'completed', data: { search_id: 9 } });

    expect(steamReconApi.getSearch).toHaveBeenCalledWith(9);
    expect(next).toMatchObject({ phase: 'completed', searchId: 9, result: persisted });
  });

  it('stores the persisted record on "cancelled" too', async () => {
    const persisted = { id: 9, status: 'cancelled', result: { profile: { steamid64: '1' } } };
    steamReconApi.getSearch.mockResolvedValue(persisted);

    const next = await reduce(running, { type: 'cancelled', data: { search_id: 9 } });

    expect(next).toMatchObject({ phase: 'cancelled', result: persisted });
  });

  it('falls back to a null result if the follow-up fetch fails', async () => {
    steamReconApi.getSearch.mockRejectedValue(new Error('network error'));

    const next = await reduce(running, { type: 'completed', data: { search_id: 9 } });

    expect(next).toMatchObject({ phase: 'completed', result: null });
  });

  it('falls back to the previous searchId on "failed" (shared failedReduce behaviour)', async () => {
    const prev = { ...running, searchId: 9 };
    const next = await reduce(prev, { type: 'failed', data: { error: 'boom' } });
    expect(next).toMatchObject({ phase: 'failed', error: 'boom', searchId: 9 });
  });
});

describe('useSteamReconScan reconcile', () => {
  it('maps a persisted completed search onto state after a dropped connection', () => {
    const prev = { ...SCAN_INITIAL_STATE, phase: 'running', target: 'robinwalker' };
    const search = { status: 'completed', result: { profile: { steamid64: '1' } } };

    expect(reconcile(prev, search)).toMatchObject({ phase: 'completed', result: search, error: '' });
  });

  it('surfaces the persisted error message when reconciling a failed search', () => {
    const prev = { ...SCAN_INITIAL_STATE, phase: 'running' };
    const search = { status: 'failed', error_message: 'Steam Web API rate limit reached' };

    expect(reconcile(prev, search)).toMatchObject({
      phase: 'failed',
      error: 'Steam Web API rate limit reached',
      result: null,
    });
  });
});

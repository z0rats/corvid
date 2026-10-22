import { reduce, reconcile } from './useTelegramScan';
import { telegramSearchApi } from '../services/api/telegramSearchApi';
import { SCAN_INITIAL_STATE } from '../state/telegramScanAtoms';

// Only this feature's event -> state mapping; the transport is useResumableScan's own test.

vi.mock('../services/api/telegramSearchApi', () => ({ telegramSearchApi: { getSearch: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('useTelegramScan reduce', () => {
  const running = { ...SCAN_INITIAL_STATE, phase: 'running', target: '@durov' };

  it('captures the searchId on "started"', async () => {
    expect(await reduce(running, { type: 'started', data: { search_id: 4 } })).toMatchObject({ searchId: 4 });
  });

  it('tracks stage, title and sampling counters on "progress"', async () => {
    const afterProfile = await reduce(running, {
      type: 'progress',
      data: { stage: 'profile_done', title: 'Pavel Durov', kind: 'channel' },
    });
    const afterPosts = await reduce(afterProfile, {
      type: 'progress',
      data: { stage: 'posts', sampled: 40, target: 100 },
    });

    expect(afterPosts).toMatchObject({ stage: 'posts', title: 'Pavel Durov', sampled: 40, sampleTarget: 100 });
  });

  it.each(['completed', 'cancelled'])('fetches the persisted record on "%s"', async (type) => {
    const persisted = { id: 4, status: type, result: { profile: { username: 'durov' } } };
    telegramSearchApi.getSearch.mockResolvedValue(persisted);

    const next = await reduce(running, { type, data: { search_id: 4 } });

    expect(telegramSearchApi.getSearch).toHaveBeenCalledWith(4);
    expect(next).toMatchObject({ phase: type, searchId: 4, result: persisted });
  });

  it('keeps a null result when the persisted record cannot be fetched', async () => {
    telegramSearchApi.getSearch.mockRejectedValue(new Error('network'));

    const next = await reduce(running, { type: 'completed', data: { search_id: 4 } });

    expect(next).toMatchObject({ phase: 'completed', result: null });
  });

  it('records the error on "failed"', async () => {
    const next = await reduce(running, {
      type: 'failed',
      data: { search_id: 4, error: 'No public Telegram channel or group named @x' },
    });

    expect(next).toMatchObject({ phase: 'failed', error: 'No public Telegram channel or group named @x' });
  });
});

describe('useTelegramScan reconcile', () => {
  it('adopts a completed record as the result', () => {
    const search = { id: 4, status: 'completed', result: {} };
    expect(reconcile(SCAN_INITIAL_STATE, search)).toMatchObject({ phase: 'completed', result: search, error: '' });
  });

  it('surfaces a failed record\'s error_message', () => {
    const next = reconcile(SCAN_INITIAL_STATE, { id: 4, status: 'failed', error_message: 'rate limited' });
    expect(next).toMatchObject({ phase: 'failed', error: 'rate limited' });
  });
});

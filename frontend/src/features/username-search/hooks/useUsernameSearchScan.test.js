import { reduce, reconcile } from './useUsernameSearchScan';
import { buildInitialState } from '../state/scanAtoms';
import { usernameSearchApi } from '../services/api/usernameSearchApi';

vi.mock('../services/api/usernameSearchApi');

// This hook plugs its own `reduce`/`reconcile` into the shared
// `useResumableScan` (see core/hooks/useResumableScan.test.js for the
// reconnect/abort/cancel-gate mechanics that hook owns) - these tests only
// cover what's specific to username-search: how one SSE event or one
// persisted run record maps onto this feature's state shape, including the
// "completed"/"cancelled" refetch some sources (social-analyzer) need
// because their terminal event carries counts but not the found-site list.

describe('useUsernameSearchScan reduce', () => {
  afterEach(() => vi.clearAllMocks());

  const running = { ...buildInitialState('maigret'), phase: 'running', username: 'alice' };

  it('captures the searchId and total site count on "started"', async () => {
    const next = await reduce(running, { type: 'started', data: { search_id: 9, total_sites: 300 } });
    expect(next).toMatchObject({ searchId: 9, totalSites: 300 });
  });

  it('appends a found site on a "progress" event that reports a hit', async () => {
    const prev = { ...running, foundSites: [{ site_name: 'GitHub', url_user: 'https://github.com/alice' }] };
    const next = await reduce(prev, {
      type: 'progress',
      data: { checked: 5, total_sites: 300, site_name: 'Reddit', found: true, url_user: 'https://reddit.com/u/alice' },
    });
    expect(next.foundSites).toEqual([
      { site_name: 'GitHub', url_user: 'https://github.com/alice' },
      { site_name: 'Reddit', url_user: 'https://reddit.com/u/alice' },
    ]);
    expect(next).toMatchObject({ checked: 5, totalSites: 300, currentSite: 'Reddit' });
  });

  it('leaves foundSites untouched on a "progress" event with no hit', async () => {
    const prev = { ...running, foundSites: [] };
    const next = await reduce(prev, { type: 'progress', data: { checked: 2, total_sites: 300, site_name: 'Vimeo', found: false } });
    expect(next.foundSites).toEqual([]);
  });

  it('refetches the persisted found-site list on "completed" (social-analyzer has no inline list)', async () => {
    usernameSearchApi.getRun.mockResolvedValue({ site_results: [{ site_name: 'GitHub', url_user: 'https://github.com/alice' }] });

    const next = await reduce(running, { type: 'completed', data: { search_id: 9, total_sites_checked: 300 } });

    expect(usernameSearchApi.getRun).toHaveBeenCalledWith(9);
    expect(next).toMatchObject({
      phase: 'completed', checked: 300, totalSites: 300, searchId: 9,
      foundSites: [{ site_name: 'GitHub', url_user: 'https://github.com/alice' }],
    });
  });

  it('keeps the previous foundSites when the refetch fails', async () => {
    usernameSearchApi.getRun.mockRejectedValue(new Error('network down'));
    const prev = { ...running, foundSites: [{ site_name: 'GitHub', url_user: 'https://github.com/alice' }] };

    const next = await reduce(prev, { type: 'completed', data: { search_id: 9, total_sites_checked: 300 } });

    expect(next.foundSites).toEqual(prev.foundSites);
  });

  it('falls back to the previous searchId on "failed" (shared failedReduce behaviour)', async () => {
    const prev = { ...running, searchId: 9 };
    const next = await reduce(prev, { type: 'failed', data: { error: 'boom' } });
    expect(next).toMatchObject({ phase: 'failed', error: 'boom', searchId: 9 });
  });
});

describe('useUsernameSearchScan reconcile', () => {
  it('maps a persisted run record onto state after a dropped connection', async () => {
    const prev = { ...buildInitialState('maigret'), phase: 'running', username: 'alice' };
    const run = {
      status: 'completed',
      total_sites_checked: 300,
      site_results: [{ site_name: 'GitHub', url_user: 'https://github.com/alice' }],
      error_message: '',
    };
    expect(await reconcile(prev, run)).toMatchObject({
      phase: 'completed', checked: 300, totalSites: 300, foundSites: run.site_results, error: '',
    });
  });
});

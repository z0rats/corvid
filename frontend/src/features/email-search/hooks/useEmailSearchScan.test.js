import { reduce, reconcile } from './useEmailSearchScan';
import { SCAN_INITIAL_STATE } from '../state/scanAtoms';

// This hook plugs its own `reduce`/`reconcile` into the shared
// `useResumableScan` (see core/hooks/useResumableScan.test.js for the
// reconnect/abort/cancel-gate mechanics that hook owns) - these tests only
// cover what's specific to email-search: how one SSE event or one persisted
// run record maps onto this feature's state shape.

describe('useEmailSearchScan reduce', () => {
  const running = { ...SCAN_INITIAL_STATE, phase: 'running', username: 'alice', searchId: null };

  it('captures the searchId and total provider count on "started"', () => {
    const next = reduce(running, { type: 'started', data: { search_id: 9, total_providers: 26 } });
    expect(next).toMatchObject({ searchId: 9, totalProviders: 26 });
  });

  it('appends a found provider on a "progress" event that reports a hit', () => {
    const prev = { ...running, foundProviders: [{ provider_name: 'gmail', emails: ['a@gmail.com'] }] };
    const next = reduce(prev, {
      type: 'progress',
      data: { checked: 5, total_providers: 26, checker_name: 'outlook', found: true, provider_name: 'outlook', emails: ['a@outlook.com'] },
    });
    expect(next.foundProviders).toEqual([
      { provider_name: 'gmail', emails: ['a@gmail.com'] },
      { provider_name: 'outlook', emails: ['a@outlook.com'] },
    ]);
    expect(next).toMatchObject({ checked: 5, totalProviders: 26, currentProvider: 'outlook' });
  });

  it('leaves foundProviders untouched on a "progress" event with no hit', () => {
    const prev = { ...running, foundProviders: [] };
    const next = reduce(prev, { type: 'progress', data: { checked: 2, total_providers: 26, checker_name: 'yahoo', found: false } });
    expect(next.foundProviders).toEqual([]);
  });

  it('marks the scan finished on "completed" and carries the checked total', () => {
    const next = reduce(running, { type: 'completed', data: { search_id: 9, total_providers_checked: 26 } });
    expect(next).toMatchObject({ phase: 'completed', checked: 26, totalProviders: 26, searchId: 9 });
  });

  it('falls back to the previous searchId on "failed" (shared failedReduce behaviour)', () => {
    const prev = { ...running, searchId: 9 };
    const next = reduce(prev, { type: 'failed', data: { error: 'boom' } });
    expect(next).toMatchObject({ phase: 'failed', error: 'boom', searchId: 9 });
  });
});

describe('useEmailSearchScan reconcile', () => {
  it('maps a persisted run record onto state after a dropped connection', () => {
    const prev = { ...SCAN_INITIAL_STATE, phase: 'running', username: 'alice' };
    const run = {
      status: 'completed',
      total_providers_checked: 26,
      provider_results: [{ provider_name: 'gmail', emails: ['a@gmail.com'] }],
      error_message: '',
    };
    expect(reconcile(prev, run)).toMatchObject({
      phase: 'completed', checked: 26, totalProviders: 26, foundProviders: run.provider_results, error: '',
    });
  });
});

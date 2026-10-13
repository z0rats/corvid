import { renderHook } from '@testing-library/react';
import { useUsernameSearchScan } from './useUsernameSearchScan';
import { useResumableScan } from '../../../core/hooks/useResumableScan';

vi.mock('../../../core/hooks/useResumableScan', async (importOriginal) => ({
  ...(await importOriginal()),
  useResumableScan: vi.fn(),
}));

describe('useUsernameSearchScan request shape', () => {
  let resumableStartScan;

  beforeEach(() => {
    resumableStartScan = vi.fn();
    useResumableScan.mockReturnValue({ startScan: resumableStartScan, cancelScan: vi.fn(), reset: vi.fn() });
  });

  afterEach(() => vi.clearAllMocks());

  it('posts a maigret scan to /scan with the run it follows', () => {
    const { result } = renderHook(() => useUsernameSearchScan('maigret'));
    result.current.startScan('alice', { tags: ['coding'], parentSearchId: 4, pivotSource: 'link on GitHub' });

    expect(useResumableScan.mock.calls[0][0].endpoint).toMatchObject({ scanPath: 'scan' });
    expect(resumableStartScan.mock.calls[0][0]).toEqual({
      username: 'alice',
      source: 'maigret',
      tags: ['coding'],
      excluded_tags: undefined,
      parent_search_id: 4,
      pivot_source: 'link on GitHub',
    });
  });

  it('posts a site check to its own /scan/site-check route with the named sites', () => {
    const { result } = renderHook(() => useUsernameSearchScan('site_check'));
    result.current.startScan('alice', { siteNames: ['Twitter'], parentSearchId: 4, pivotSource: 'p' });

    expect(useResumableScan.mock.calls[0][0]).toMatchObject({
      scopeKey: 'username-search-site_check',
      endpoint: { base: '/api/username-search', scanPath: 'scan/site-check' },
    });
    const [body, seed] = resumableStartScan.mock.calls[0];
    expect(body).toEqual({ username: 'alice', site_names: ['Twitter'], parent_search_id: 4, pivot_source: 'p' });
    expect(seed).toMatchObject({ phase: 'running', username: 'alice', siteNames: ['Twitter'] });
  });
});

import { act, renderHook } from '@testing-library/react';
import baseApi from '../../../../core/services/baseApi';
import { useSetAtom } from 'jotai';
import { useInstagramScan } from './useInstagramScan';
import { instagramScanStateAtom, INSTAGRAM_SCAN_INITIAL_STATE } from '../../state/instagramScanAtoms';

vi.mock('../../../../core/services/baseApi', () => ({ default: { get: vi.fn(), post: vi.fn() }, baseURL: '' }));
vi.mock('../../services/api/instagramSearchApi');

// instagramScanStateAtom is module-scoped (see instagramScanAtoms.js), so it
// doesn't reset between tests on its own - every test below sets it explicitly
// via this harness rather than relying on a fresh default.
function useTestHarness() {
  const scanHook = useInstagramScan();
  const setState = useSetAtom(instagramScanStateAtom);
  return { ...scanHook, setState };
}

describe('useInstagramScan — cancelScan', () => {
  afterEach(() => vi.clearAllMocks());

  // The running/searchId gate itself is exercised generically in
  // core/hooks/useResumableScan.test.js - this only checks useInstagramScan
  // wires its own instagramSearchApi.cancelScan into that gate.
  it("cancels the running scan through this feature's endpoint", async () => {
    baseApi.post.mockResolvedValue({});
    const { result } = renderHook(() => useTestHarness());

    act(() => {
      result.current.setState({ ...INSTAGRAM_SCAN_INITIAL_STATE, loading: true, searchId: 42 });
    });

    await act(async () => {
      result.current.cancelScan();
    });

    expect(baseApi.post).toHaveBeenCalledWith('/api/instagram-search/history/42/cancel');
  });
});

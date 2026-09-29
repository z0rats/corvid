import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useInstagramScan } from './useInstagramScan';
import { instagramScanStateAtom, INSTAGRAM_SCAN_INITIAL_STATE } from '../../state/instagramScanAtoms';
import { instagramSearchApi } from '../../services/api/instagramSearchApi';

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
  it("wires cancelScan to instagramSearchApi.cancelScan with the running scan's searchId", async () => {
    instagramSearchApi.cancelScan.mockResolvedValue(undefined);
    const { result } = renderHook(() => useTestHarness());

    act(() => {
      result.current.setState({ ...INSTAGRAM_SCAN_INITIAL_STATE, loading: true, searchId: 42 });
    });

    await act(async () => {
      result.current.cancelScan();
    });

    expect(instagramSearchApi.cancelScan).toHaveBeenCalledWith(42);
  });
});

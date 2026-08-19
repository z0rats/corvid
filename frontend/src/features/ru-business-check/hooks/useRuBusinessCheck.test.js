import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useRuBusinessCheck } from './useRuBusinessCheck';
import { ruBusinessCheckStateAtom, RU_BUSINESS_CHECK_INITIAL_STATE } from '../state/ruBusinessCheckAtoms';
import { ruBusinessCheckApi } from '../services/api/ruBusinessCheckApi';

vi.mock('../services/api/ruBusinessCheckApi');

// ruBusinessCheckStateAtom is module-scoped (see ruBusinessCheckAtoms.js), so it doesn't
// reset between tests on its own - every test below sets it explicitly via this harness
// rather than relying on a fresh default.
function useTestHarness() {
  const ruBusinessCheck = useRuBusinessCheck();
  const setState = useSetAtom(ruBusinessCheckStateAtom);
  return { ...ruBusinessCheck, setState };
}

describe('useRuBusinessCheck — cancelScan', () => {
  afterEach(() => vi.clearAllMocks());

  // The running/searchId gate itself (no scan running, already finished, the
  // `loading`-vs-`phase` state-shape fallback) is exercised generically in
  // core/hooks/useResumableScan.test.js - this only checks useRuBusinessCheck
  // wires its own ruBusinessCheckApi.cancelScan into that gate.
  it("wires cancelScan to ruBusinessCheckApi.cancelScan with the running scan's searchId", async () => {
    ruBusinessCheckApi.cancelScan.mockResolvedValue(undefined);
    const { result } = renderHook(() => useTestHarness());

    act(() => {
      result.current.setState({ ...RU_BUSINESS_CHECK_INITIAL_STATE, loading: true, searchId: 42 });
    });

    await act(async () => {
      result.current.cancelScan();
    });

    expect(ruBusinessCheckApi.cancelScan).toHaveBeenCalledWith(42);
  });
});

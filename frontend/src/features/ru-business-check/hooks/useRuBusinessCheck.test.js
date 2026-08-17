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

  it("exposes cancelScan and calls the API with the running scan's searchId", async () => {
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

  it('does not call the API when no scan is running', async () => {
    const { result } = renderHook(() => useTestHarness());

    act(() => {
      result.current.setState(RU_BUSINESS_CHECK_INITIAL_STATE);
    });

    await act(async () => {
      result.current.cancelScan();
    });

    expect(ruBusinessCheckApi.cancelScan).not.toHaveBeenCalled();
  });

  it('does not call the API once the scan has already finished (loading: false)', async () => {
    const { result } = renderHook(() => useTestHarness());

    act(() => {
      result.current.setState({ ...RU_BUSINESS_CHECK_INITIAL_STATE, loading: false, searchId: 42 });
    });

    await act(async () => {
      result.current.cancelScan();
    });

    expect(ruBusinessCheckApi.cancelScan).not.toHaveBeenCalled();
  });
});

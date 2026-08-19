import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useGitRecon } from './useGitRecon';
import { gitReconStateAtom, GIT_RECON_INITIAL_STATE } from '../state/gitReconAtoms';
import { gitReconApi } from '../services/api/gitReconApi';

vi.mock('../services/api/gitReconApi');

// gitReconStateAtom is module-scoped (see gitReconAtoms.js), so it doesn't
// reset between tests on its own - every test below sets it explicitly via
// this harness rather than relying on a fresh default.
function useTestHarness() {
  const gitRecon = useGitRecon();
  const setState = useSetAtom(gitReconStateAtom);
  return { ...gitRecon, setState };
}

describe('useGitRecon — cancelScan', () => {
  afterEach(() => vi.clearAllMocks());

  // The running/searchId gate itself (no scan running, already finished, the
  // `loading`-vs-`phase` state-shape fallback) is exercised generically in
  // core/hooks/useResumableScan.test.js - this only checks useGitRecon wires
  // its own gitReconApi.cancelScan into that gate.
  it("wires cancelScan to gitReconApi.cancelScan with the running scan's searchId", async () => {
    gitReconApi.cancelScan.mockResolvedValue(undefined);
    const { result } = renderHook(() => useTestHarness());

    act(() => {
      result.current.setState({ ...GIT_RECON_INITIAL_STATE, loading: true, searchId: 42 });
    });

    await act(async () => {
      result.current.cancelScan();
    });

    expect(gitReconApi.cancelScan).toHaveBeenCalledWith(42);
  });
});

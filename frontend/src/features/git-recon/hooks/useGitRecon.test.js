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

  it('exposes cancelScan and calls the API with the running scan\'s searchId', async () => {
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

  it('does not call the API when no scan is running', async () => {
    const { result } = renderHook(() => useTestHarness());

    act(() => {
      result.current.setState(GIT_RECON_INITIAL_STATE);
    });

    await act(async () => {
      result.current.cancelScan();
    });

    expect(gitReconApi.cancelScan).not.toHaveBeenCalled();
  });

  it('does not call the API once the scan has already finished (loading: false)', async () => {
    const { result } = renderHook(() => useTestHarness());

    act(() => {
      result.current.setState({ ...GIT_RECON_INITIAL_STATE, loading: false, searchId: 42 });
    });

    await act(async () => {
      result.current.cancelScan();
    });

    expect(gitReconApi.cancelScan).not.toHaveBeenCalled();
  });
});

import { act, renderHook, waitFor } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useEmailAnalysis } from './useEmailAnalysis';
import { emailAnalyzerApi } from '../../services/api/emailAnalyzerApi';
import { emailAnalysisStateAtom, EMAIL_ANALYSIS_INITIAL_STATE } from '../../state/emailAnalysisAtoms';

vi.mock('../../services/api/emailAnalyzerApi');

// emailAnalysisStateAtom is module-scoped, so it doesn't reset between tests on its own.
function resetEmailAnalysisState() {
  const { result } = renderHook(() => useSetAtom(emailAnalysisStateAtom));
  act(() => result.current(EMAIL_ANALYSIS_INITIAL_STATE));
}

beforeEach(resetEmailAnalysisState);
afterEach(() => {
  vi.clearAllMocks();
  vi.useRealTimers();
});

describe('useEmailAnalysis — analyzeEmail', () => {
  it('sets an error and does nothing else when no file is given', async () => {
    const { result } = renderHook(() => useEmailAnalysis());

    await act(async () => result.current.analyzeEmail(null));

    expect(result.current.error).toBe('No file provided');
    expect(emailAnalyzerApi.analyzeEmail).not.toHaveBeenCalled();
  });

  it('resolves to the analysis result and clears loading', async () => {
    emailAnalyzerApi.analyzeEmail.mockResolvedValue({ summary: 'clean' });
    const { result } = renderHook(() => useEmailAnalysis());
    const file = new File(['content'], 'sample.eml');

    let promise;
    act(() => { promise = result.current.analyzeEmail(file); });
    expect(result.current.isLoading).toBe(true);
    await act(async () => promise);
    await waitFor(() => expect(result.current.isLoading).toBe(false), { timeout: 2000 });

    expect(emailAnalyzerApi.analyzeEmail).toHaveBeenCalledWith(file);
    expect(result.current.result).toEqual({ summary: 'clean' });
    expect(result.current.error).toBeNull();
  });

  it('surfaces the API error message and clears loading', async () => {
    emailAnalyzerApi.analyzeEmail.mockRejectedValue(new Error('parse failed'));
    const { result } = renderHook(() => useEmailAnalysis());
    const file = new File(['content'], 'sample.eml');

    await act(async () => result.current.analyzeEmail(file));

    expect(result.current.error).toBe('parse failed');
    expect(result.current.isLoading).toBe(false);
    expect(result.current.uploadProgress).toBe(0);
  });

  it('aborts a stale in-flight analysis when a new one starts, so only the newest result lands', async () => {
    let resolveFirst;
    emailAnalyzerApi.analyzeEmail
      .mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve; }))
      .mockResolvedValueOnce({ summary: 'second' });
    const { result } = renderHook(() => useEmailAnalysis());
    const file = new File(['content'], 'sample.eml');

    act(() => { result.current.analyzeEmail(file); });
    await waitFor(() => expect(result.current.isLoading).toBe(true));

    await act(async () => result.current.analyzeEmail(file));
    await waitFor(() => expect(result.current.isLoading).toBe(false), { timeout: 2000 });
    expect(result.current.result).toEqual({ summary: 'second' });

    // The first call's late resolution must not overwrite the second result.
    await act(async () => resolveFirst({ summary: 'first' }));
    expect(result.current.result).toEqual({ summary: 'second' });
  });
});

describe('useEmailAnalysis — reset', () => {
  it('restores the initial state', async () => {
    emailAnalyzerApi.analyzeEmail.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useEmailAnalysis());
    await act(async () => result.current.analyzeEmail(new File(['x'], 'x.eml')));
    expect(result.current.error).toBe('boom');

    act(() => result.current.reset());

    expect(result.current).toMatchObject({
      result: null,
      isLoading: false,
      error: null,
      uploadProgress: 0,
    });
  });
});

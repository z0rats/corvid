import { renderHook, waitFor } from '@testing-library/react';
import { useTemporalAnalysis } from './useTemporalAnalysis';
import { temporalAnalysisApi } from '../../services/api/temporalAnalysisApi';

vi.mock('../../services/api/temporalAnalysisApi');

afterEach(() => vi.clearAllMocks());

describe('useTemporalAnalysis', () => {
  it('does nothing when no domain is given', () => {
    const { result } = renderHook(() => useTemporalAnalysis(''));
    expect(temporalAnalysisApi.lookupTemporalAnalysis).not.toHaveBeenCalled();
    expect(result.current.data).toBeNull();
  });

  it('fetches the timeline for a plain domain', async () => {
    temporalAnalysisApi.lookupTemporalAnalysis.mockResolvedValue({ events: [], sources_failed: [] });
    const { result } = renderHook(() => useTemporalAnalysis('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ events: [], sources_failed: [] });
  });

  it('marks a wildcard pattern as unsupported without calling the API', () => {
    const { result } = renderHook(() => useTemporalAnalysis('*.example.com'));
    expect(result.current.unsupported).toBe(true);
    expect(temporalAnalysisApi.lookupTemporalAnalysis).not.toHaveBeenCalled();
  });

  it('extracts an error message on failure', async () => {
    temporalAnalysisApi.lookupTemporalAnalysis.mockRejectedValue({ message: 'network down' });
    const { result } = renderHook(() => useTemporalAnalysis('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('network down');
  });

  it('refetches when the domain changes', async () => {
    temporalAnalysisApi.lookupTemporalAnalysis.mockResolvedValue({ events: [] });
    const { rerender } = renderHook(({ domain }) => useTemporalAnalysis(domain), {
      initialProps: { domain: 'example.com' }
    });

    await waitFor(() => expect(temporalAnalysisApi.lookupTemporalAnalysis).toHaveBeenCalledWith('example.com'));

    rerender({ domain: 'other.com' });
    await waitFor(() => expect(temporalAnalysisApi.lookupTemporalAnalysis).toHaveBeenCalledWith('other.com'));
  });
});

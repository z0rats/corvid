import { act, renderHook, waitFor } from '@testing-library/react';
import { useHostProbe } from './useHostProbe';
import { hostProbeApi } from '../../services/api/hostProbeApi';

vi.mock('../../services/api/hostProbeApi');

describe('useHostProbe', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no data and no error', () => {
    const { result } = renderHook(() => useHostProbe('example.com'));

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.unsupported).toBe(false);
  });

  it('marks a wildcard domain as unsupported', () => {
    const { result } = renderHook(() => useHostProbe('example-*'));

    expect(result.current.unsupported).toBe(true);
  });

  it('populates data on a successful run', async () => {
    const mockResult = { domain: 'example.com', reachable: true, results: [] };
    hostProbeApi.probeHost.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useHostProbe('example.com'));

    await act(async () => {
      await result.current.run();
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(mockResult);
    expect(result.current.error).toBeNull();
    expect(hostProbeApi.probeHost).toHaveBeenCalledWith('example.com');
  });

  it('surfaces the API error message on failure', async () => {
    hostProbeApi.probeHost.mockRejectedValue({
      response: { data: { detail: 'httpx is not installed' } },
    });

    const { result } = renderHook(() => useHostProbe('example.com'));

    await act(async () => {
      await result.current.run();
    });

    expect(result.current.error).toBe('httpx is not installed');
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});

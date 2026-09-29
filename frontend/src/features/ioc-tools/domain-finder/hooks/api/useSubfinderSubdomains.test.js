import { act, renderHook, waitFor } from '@testing-library/react';
import { useSubfinderSubdomains } from './useSubfinderSubdomains';
import { subfinderApi } from '../../services/api/subfinderApi';

vi.mock('../../services/api/subfinderApi');

describe('useSubfinderSubdomains', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no data and no error', () => {
    const { result } = renderHook(() => useSubfinderSubdomains('example.com'));

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.unsupported).toBe(false);
  });

  it('marks a wildcard domain as unsupported', () => {
    const { result } = renderHook(() => useSubfinderSubdomains('example-*'));

    expect(result.current.unsupported).toBe(true);
  });

  it('populates data on a successful run', async () => {
    const mockResult = { domain: 'example.com', subdomains: ['www.example.com'] };
    subfinderApi.lookupSubfinderSubdomains.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useSubfinderSubdomains('example.com'));

    await act(async () => {
      await result.current.run();
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(mockResult);
    expect(result.current.error).toBeNull();
    expect(subfinderApi.lookupSubfinderSubdomains).toHaveBeenCalledWith('example.com');
  });

  it('surfaces the API error message on failure', async () => {
    subfinderApi.lookupSubfinderSubdomains.mockRejectedValue({
      response: { data: { detail: 'subfinder is not installed' } },
    });

    const { result } = renderHook(() => useSubfinderSubdomains('example.com'));

    await act(async () => {
      await result.current.run();
    });

    expect(result.current.error).toBe('subfinder is not installed');
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});

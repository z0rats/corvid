import { renderHook, waitFor } from '@testing-library/react';
import { useDnsDumpster } from './useDnsDumpster';
import { dnsDumpsterApi } from '../../services/api/dnsDumpsterApi';

vi.mock('../../services/api/dnsDumpsterApi');

afterEach(() => vi.clearAllMocks());

describe('useDnsDumpster', () => {
  it('does nothing when no domain is given', () => {
    const { result } = renderHook(() => useDnsDumpster(''));
    expect(dnsDumpsterApi.lookupDnsDumpster).not.toHaveBeenCalled();
    expect(result.current.data).toBeNull();
  });

  it('fetches data for a plain domain', async () => {
    dnsDumpsterApi.lookupDnsDumpster.mockResolvedValue({ hosts: ['a.example.com'] });
    const { result } = renderHook(() => useDnsDumpster('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ hosts: ['a.example.com'] });
    expect(result.current.notConfigured).toBe(false);
  });

  it('marks a wildcard pattern as unsupported without calling the API', () => {
    const { result } = renderHook(() => useDnsDumpster('*.example.com'));
    expect(result.current.unsupported).toBe(true);
    expect(dnsDumpsterApi.lookupDnsDumpster).not.toHaveBeenCalled();
  });

  it('sets notConfigured (not error) when the key is missing', async () => {
    dnsDumpsterApi.lookupDnsDumpster.mockRejectedValue({
      response: { data: { error_code: 'DNSDUMPSTER_NOT_CONFIGURED' } },
    });
    const { result } = renderHook(() => useDnsDumpster('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.notConfigured).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('sets a normal error for any other failure', async () => {
    dnsDumpsterApi.lookupDnsDumpster.mockRejectedValue({
      response: { data: { detail: 'upstream error' } },
    });
    const { result } = renderHook(() => useDnsDumpster('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('upstream error');
    expect(result.current.notConfigured).toBe(false);
  });
});

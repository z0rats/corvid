import { renderHook, waitFor } from '@testing-library/react';
import { useWaybackLookup } from './useWaybackLookup';
import { waybackApi } from '../../services/api/waybackApi';

vi.mock('../../services/api/waybackApi');

afterEach(() => vi.clearAllMocks());

describe('useWaybackLookup', () => {
  it('does nothing when no domain is given', () => {
    const { result } = renderHook(() => useWaybackLookup(''));
    expect(waybackApi.lookupWayback).not.toHaveBeenCalled();
    expect(result.current.data).toBeNull();
  });

  it('fetches snapshots for a plain domain', async () => {
    waybackApi.lookupWayback.mockResolvedValue({ snapshots: [], total_snapshots: 0 });
    const { result } = renderHook(() => useWaybackLookup('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ snapshots: [], total_snapshots: 0 });
  });

  it('marks a wildcard pattern as unsupported without calling the API', () => {
    const { result } = renderHook(() => useWaybackLookup('*.example.com'));
    expect(result.current.unsupported).toBe(true);
    expect(waybackApi.lookupWayback).not.toHaveBeenCalled();
  });

  it('extracts an error message on failure', async () => {
    waybackApi.lookupWayback.mockRejectedValue({ message: 'network down' });
    const { result } = renderHook(() => useWaybackLookup('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('network down');
  });

  it('passes the path through and refetches when it changes', async () => {
    waybackApi.lookupWayback.mockResolvedValue({ snapshots: [] });
    const { result, rerender } = renderHook(
      ({ domain, path }) => useWaybackLookup(domain, path),
      { initialProps: { domain: 'example.com', path: null } }
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(waybackApi.lookupWayback).toHaveBeenCalledWith('example.com', null);

    rerender({ domain: 'example.com', path: '/login' });
    await waitFor(() => expect(waybackApi.lookupWayback).toHaveBeenCalledWith('example.com', '/login'));
  });
});

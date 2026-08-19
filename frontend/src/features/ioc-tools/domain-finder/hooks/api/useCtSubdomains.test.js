import { renderHook, waitFor } from '@testing-library/react';
import { useCtSubdomains } from './useCtSubdomains';
import { ctSubdomainsApi } from '../../services/api/ctSubdomainsApi';

vi.mock('../../services/api/ctSubdomainsApi');

afterEach(() => vi.clearAllMocks());

describe('useCtSubdomains', () => {
  it('does nothing when no domain is given', () => {
    const { result } = renderHook(() => useCtSubdomains(''));
    expect(ctSubdomainsApi.lookupCtSubdomains).not.toHaveBeenCalled();
    expect(result.current.data).toBeNull();
  });

  it('fetches subdomains for a plain domain', async () => {
    ctSubdomainsApi.lookupCtSubdomains.mockResolvedValue({ subdomains: ['www.example.com'] });
    const { result } = renderHook(() => useCtSubdomains('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ subdomains: ['www.example.com'] });
  });

  it('marks a wildcard pattern as unsupported without calling the API', () => {
    const { result } = renderHook(() => useCtSubdomains('*.example.com'));
    expect(result.current.unsupported).toBe(true);
    expect(ctSubdomainsApi.lookupCtSubdomains).not.toHaveBeenCalled();
  });

  it('extracts an error message on failure', async () => {
    ctSubdomainsApi.lookupCtSubdomains.mockRejectedValue({ message: 'network down' });
    const { result } = renderHook(() => useCtSubdomains('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('network down');
  });
});

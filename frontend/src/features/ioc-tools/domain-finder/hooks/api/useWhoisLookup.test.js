import { renderHook, waitFor } from '@testing-library/react';
import { useWhoisLookup } from './useWhoisLookup';
import { whoisLookupApi } from '../../services/api/whoisLookupApi';

vi.mock('../../services/api/whoisLookupApi');

afterEach(() => vi.clearAllMocks());

describe('useWhoisLookup', () => {
  it('does nothing when no domain is given', () => {
    const { result } = renderHook(() => useWhoisLookup(''));
    expect(whoisLookupApi.lookupWhois).not.toHaveBeenCalled();
    expect(result.current.data).toBeNull();
  });

  it('fetches whois data for a plain domain', async () => {
    whoisLookupApi.lookupWhois.mockResolvedValue({ registrar: 'Example Registrar' });
    const { result } = renderHook(() => useWhoisLookup('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ registrar: 'Example Registrar' });
  });

  it('marks a wildcard pattern as unsupported without calling the API', () => {
    const { result } = renderHook(() => useWhoisLookup('exam?le.com'));
    expect(result.current.unsupported).toBe(true);
    expect(whoisLookupApi.lookupWhois).not.toHaveBeenCalled();
  });

  it('extracts the error detail from a failed response', async () => {
    whoisLookupApi.lookupWhois.mockRejectedValue({ response: { data: { message: 'WHOIS server timeout' } } });
    const { result } = renderHook(() => useWhoisLookup('example.com'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('WHOIS server timeout');
  });
});

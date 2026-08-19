import { renderHook, waitFor } from '@testing-library/react';
import { useServiceFetcher } from './useServiceFetcher';
import { iocLookupApi } from '../../../../shared/services/api/iocLookupApi';

vi.mock('../../../../shared/services/api/iocLookupApi');

afterEach(() => vi.clearAllMocks());

const serviceConfigEntry = {
  key: 'abuseipdb',
  name: 'AbuseIPDB',
  getSummaryAndTlp: (data) => ({ summary: `score ${data.score}`, tlp: 'GREEN' }),
};

describe('useServiceFetcher — success path', () => {
  it('fetches, stores the result, and derives display props via the service config', async () => {
    iocLookupApi.lookupSingleService.mockResolvedValue({ data: { score: 42 } });
    const { result } = renderHook(() => useServiceFetcher('1.2.3.4', 'ip', serviceConfigEntry, null));

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(iocLookupApi.lookupSingleService).toHaveBeenCalledWith(
      'abuseipdb',
      '1.2.3.4',
      'ip',
      expect.objectContaining({ signal: expect.anything() }),
    );
    expect(result.current.apiResult).toEqual({ score: 42 });
    expect(result.current.displayProps).toEqual({ summary: 'score 42', tlp: 'GREEN' });
  });

  it('reports the result to onResult with status "found"', async () => {
    iocLookupApi.lookupSingleService.mockResolvedValue({ data: { score: 42 } });
    const onResult = vi.fn();
    renderHook(() => useServiceFetcher('1.2.3.4', 'ip', serviceConfigEntry, onResult));

    await waitFor(() => expect(onResult).toHaveBeenCalled());

    expect(onResult).toHaveBeenCalledWith('abuseipdb', {
      service_name: 'AbuseIPDB',
      status: 'found',
      summary: 'score 42',
      tlp: 'GREEN',
      data: { score: 42 },
    });
  });
});

describe('useServiceFetcher — response.error handling', () => {
  it('maps a "not found"-shaped error to a notFound result', async () => {
    iocLookupApi.lookupSingleService.mockResolvedValue({ error: 'Resource not found', status: 404 });
    const onResult = vi.fn();
    const { result } = renderHook(() => useServiceFetcher('1.2.3.4', 'ip', serviceConfigEntry, onResult));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.apiResult).toEqual({ notFound: true, message: 'Resource not found' });
    expect(onResult).toHaveBeenCalledWith('abuseipdb', expect.objectContaining({ status: 'not_found' }));
  });

  it('maps any other API error to an error result', async () => {
    iocLookupApi.lookupSingleService.mockResolvedValue({ error: 'Rate limited', status: 429 });
    const onResult = vi.fn();
    const { result } = renderHook(() => useServiceFetcher('1.2.3.4', 'ip', serviceConfigEntry, onResult));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.apiResult).toEqual({ error: 429, message: 'Rate limited' });
    expect(onResult).toHaveBeenCalledWith('abuseipdb', expect.objectContaining({ status: 'error' }));
  });
});

describe('useServiceFetcher — thrown errors', () => {
  it('shapes a network exception into an error result', async () => {
    iocLookupApi.lookupSingleService.mockRejectedValue(new Error('Network Error'));
    const { result } = renderHook(() => useServiceFetcher('1.2.3.4', 'ip', serviceConfigEntry, null));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.apiResult).toEqual({ error: 'NETWORK_ERROR', message: 'Network Error' });
  });

  it('prefers the response detail message when present', async () => {
    iocLookupApi.lookupSingleService.mockRejectedValue({
      response: { status: 500, data: { detail: 'upstream failure' } },
      message: 'Request failed',
    });
    const { result } = renderHook(() => useServiceFetcher('1.2.3.4', 'ip', serviceConfigEntry, null));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.apiResult).toMatchObject({ error: 500, message: 'upstream failure' });
  });

  it('ignores an AbortError without setting an error result', async () => {
    const abortError = new Error('aborted');
    abortError.name = 'AbortError';
    iocLookupApi.lookupSingleService.mockRejectedValue(abortError);
    const { result } = renderHook(() => useServiceFetcher('1.2.3.4', 'ip', serviceConfigEntry, null));

    // Give the rejected promise a tick to settle without ever reaching "not loading".
    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(result.current.apiResult).toBeNull();
  });
});

describe('useServiceFetcher — no service key configured', () => {
  it('reports a 500 error without calling the API', async () => {
    const entryWithNoKey = { name: 'Broken Service' };
    const { result } = renderHook(() => useServiceFetcher('1.2.3.4', 'ip', entryWithNoKey, null));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(iocLookupApi.lookupSingleService).not.toHaveBeenCalled();
    expect(result.current.apiResult).toEqual({
      error: 500,
      message: 'No service key configured for Broken Service.',
    });
  });
});

describe('useServiceFetcher — getSummaryAndTlp failures', () => {
  it('falls back to a generic error summary when getSummaryAndTlp itself throws', async () => {
    iocLookupApi.lookupSingleService.mockResolvedValue({ data: { score: 1 } });
    const throwingEntry = {
      key: 'x',
      name: 'X',
      getSummaryAndTlp: () => {
        throw new Error('boom');
      },
    };
    const { result } = renderHook(() => useServiceFetcher('1.2.3.4', 'ip', throwingEntry, null));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.displayProps).toEqual({ summary: 'Error processing result', tlp: 'WHITE' });
  });

  it('falls back to a generic summary when the service has no getSummaryAndTlp at all', async () => {
    iocLookupApi.lookupSingleService.mockResolvedValue({ data: { score: 1 } });
    const bareEntry = { key: 'x', name: 'X' };
    const { result } = renderHook(() => useServiceFetcher('1.2.3.4', 'ip', bareEntry, null));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.displayProps).toEqual({
      summary: 'Data received, no summary available',
      tlp: 'BLUE',
    });
  });
});

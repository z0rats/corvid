import api, { baseURL } from '../../../../../core/services/baseApi';
import { getAccessToken } from '../../../../../core/utils/accessToken';
import { iocLookupApi } from './iocLookupApi';

vi.mock('../../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), patch: vi.fn() },
  baseURL: 'http://backend.test',
}));
vi.mock('../../../../../core/utils/accessToken', () => ({ getAccessToken: vi.fn() }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('iocLookupApi.fetchServiceDefinitions', () => {
  it('returns the serviceDefinitions map', async () => {
    api.get.mockResolvedValue({ data: { serviceDefinitions: { virustotal: {} } } });

    const result = await iocLookupApi.fetchServiceDefinitions();

    expect(api.get).toHaveBeenCalledWith('/api/ioc/service-definitions');
    expect(result).toEqual({ virustotal: {} });
  });

  it('falls back to an empty object when serviceDefinitions is missing', async () => {
    api.get.mockResolvedValue({ data: {} });

    const result = await iocLookupApi.fetchServiceDefinitions();

    expect(result).toEqual({});
  });
});

describe('iocLookupApi.lookupSingleService', () => {
  it('builds the URL with encoded ioc and ioc_type query params', async () => {
    api.get.mockResolvedValue({ data: { result: 'clean' } });

    const result = await iocLookupApi.lookupSingleService('virustotal', '1.2.3.4', 'ip address');

    expect(api.get).toHaveBeenCalledWith(
      '/api/ioc/lookup/virustotal?ioc=1.2.3.4&ioc_type=ip%20address',
      { signal: undefined }
    );
    expect(result).toEqual({ result: 'clean' });
  });
});

describe('iocLookupApi.fetchNewsfeedMentions', () => {
  it('requests newsfeed mentions for the given ioc', async () => {
    api.get.mockResolvedValue({ data: { mentions: [] } });

    const result = await iocLookupApi.fetchNewsfeedMentions('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/ioc/newsfeed-mentions', {
      params: { ioc: 'example.com' },
      signal: undefined,
    });
    expect(result).toEqual({ mentions: [] });
  });
});

describe('iocLookupApi.bulkLookup', () => {
  it('opens an SSE POST stream with the bearer token and iocs/services payload', async () => {
    getAccessToken.mockReturnValue('tok123');
    const body = {};
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body });
    vi.stubGlobal('fetch', fetchMock);

    const result = await iocLookupApi.bulkLookup(['1.2.3.4'], ['virustotal']);

    expect(fetchMock).toHaveBeenCalledWith(`${baseURL}/api/ioc-lookup/bulk`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer tok123',
      },
      body: JSON.stringify({ iocs: ['1.2.3.4'], services: ['virustotal'] }),
    });
    expect(result).toBe(body);
  });

  it('throws when the response is not ok', async () => {
    getAccessToken.mockReturnValue('tok123');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, statusText: 'Bad Gateway' }));

    await expect(iocLookupApi.bulkLookup(['1.2.3.4'], ['virustotal'])).rejects.toThrow(
      'Server error: Bad Gateway'
    );
  });
});

describe('iocLookupApi.fetchBulkLookupSettings', () => {
  it('requests the bulk-lookup-eligible api keys', async () => {
    api.get.mockResolvedValue({ data: { virustotal: true } });

    const result = await iocLookupApi.fetchBulkLookupSettings();

    expect(api.get).toHaveBeenCalledWith('/api/apikeys/bulk_ioc_lookup');
    expect(result).toEqual({ virustotal: true });
  });

  it('falls back to an empty object when data is missing', async () => {
    api.get.mockResolvedValue({ data: null });

    const result = await iocLookupApi.fetchBulkLookupSettings();

    expect(result).toEqual({});
  });
});

describe('iocLookupApi.updateBulkLookupSetting', () => {
  it('patches the bulk_ioc_lookup flag for the given key', async () => {
    api.patch.mockResolvedValue({ data: { bulk_ioc_lookup: true } });

    const result = await iocLookupApi.updateBulkLookupSetting('virustotal', true);

    expect(api.patch).toHaveBeenCalledWith('/api/apikeys/virustotal/bulk_ioc_lookup', {
      bulk_ioc_lookup: true,
    });
    expect(result).toEqual({ bulk_ioc_lookup: true });
  });
});

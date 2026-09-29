import { geolocationHistoryApi } from './geolocationHistoryApi';
import api, { baseURL } from '../../../../core/services/baseApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), delete: vi.fn() },
  baseURL: 'https://corvid.test',
}));

afterEach(() => vi.clearAllMocks());

describe('geolocationHistoryApi.listSearches', () => {
  it('defaults to skip=0, limit=100', async () => {
    api.get.mockResolvedValue({ data: [] });

    await geolocationHistoryApi.listSearches();

    expect(api.get).toHaveBeenCalledWith('/api/image/geolocate/history', {
      params: { skip: 0, limit: 100 },
    });
  });

  it('passes through explicit pagination params', async () => {
    api.get.mockResolvedValue({ data: [] });

    await geolocationHistoryApi.listSearches(20, 10);

    expect(api.get).toHaveBeenCalledWith('/api/image/geolocate/history', {
      params: { skip: 20, limit: 10 },
    });
  });
});

describe('geolocationHistoryApi.getSearch', () => {
  it('gets a single search by id', async () => {
    api.get.mockResolvedValue({ data: { id: 5 } });

    const result = await geolocationHistoryApi.getSearch(5);

    expect(api.get).toHaveBeenCalledWith('/api/image/geolocate/history/5');
    expect(result).toEqual({ id: 5 });
  });
});

describe('geolocationHistoryApi.deleteSearch', () => {
  it('deletes a search by id', async () => {
    api.delete.mockResolvedValue({});

    await geolocationHistoryApi.deleteSearch(5);

    expect(api.delete).toHaveBeenCalledWith('/api/image/geolocate/history/5');
  });
});

describe('geolocationHistoryApi.reportUrl', () => {
  it('builds the report URL with a format query param', () => {
    const url = geolocationHistoryApi.reportUrl(5, 'pdf');
    expect(url).toBe(`${baseURL}/api/image/geolocate/history/5/report?format=pdf`);
  });
});

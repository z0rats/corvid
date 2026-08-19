import { lookupHistoryApi } from './lookupHistoryApi';
import api, { baseURL } from '../../../../../../core/services/baseApi';

vi.mock('../../../../../../core/services/baseApi', () => ({
  default: { post: vi.fn(), get: vi.fn(), delete: vi.fn() },
  baseURL: 'https://corvid.test',
}));

afterEach(() => vi.clearAllMocks());

describe('lookupHistoryApi.saveSearch', () => {
  it('posts the ioc/type/results and returns the response data', async () => {
    api.post.mockResolvedValue({ data: { id: 1 } });

    const result = await lookupHistoryApi.saveSearch('1.2.3.4', 'ip', { found: true });

    expect(api.post).toHaveBeenCalledWith('/api/ioc-lookup/history', {
      ioc: '1.2.3.4',
      ioc_type: 'ip',
      results: { found: true },
    });
    expect(result).toEqual({ id: 1 });
  });
});

describe('lookupHistoryApi.listSearches', () => {
  it('defaults to skip=0, limit=100', async () => {
    api.get.mockResolvedValue({ data: [] });

    await lookupHistoryApi.listSearches();

    expect(api.get).toHaveBeenCalledWith('/api/ioc-lookup/history', { params: { skip: 0, limit: 100 } });
  });

  it('passes through explicit pagination params', async () => {
    api.get.mockResolvedValue({ data: [] });

    await lookupHistoryApi.listSearches(20, 10);

    expect(api.get).toHaveBeenCalledWith('/api/ioc-lookup/history', { params: { skip: 20, limit: 10 } });
  });
});

describe('lookupHistoryApi.getSearch', () => {
  it('gets a single search by id', async () => {
    api.get.mockResolvedValue({ data: { id: 5 } });

    const result = await lookupHistoryApi.getSearch(5);

    expect(api.get).toHaveBeenCalledWith('/api/ioc-lookup/history/5');
    expect(result).toEqual({ id: 5 });
  });
});

describe('lookupHistoryApi.deleteSearch', () => {
  it('deletes a search by id', async () => {
    api.delete.mockResolvedValue({});

    await lookupHistoryApi.deleteSearch(5);

    expect(api.delete).toHaveBeenCalledWith('/api/ioc-lookup/history/5');
  });
});

describe('lookupHistoryApi.reportUrl', () => {
  it('builds the report URL with format and locale query params', () => {
    const url = lookupHistoryApi.reportUrl(5, 'pdf', 'en');
    expect(url).toBe(`${baseURL}/api/ioc-lookup/history/5/report?format=pdf&locale=en`);
  });
});

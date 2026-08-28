import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';
import { ruBusinessCheckApi } from './ruBusinessCheckApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
  baseURL: 'http://backend.test',
}));
vi.mock('../../../../core/utils/accessToken', () => ({ getAccessToken: vi.fn() }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('ruBusinessCheckApi.startScan', () => {
  it('opens an SSE POST stream with the bearer token and the given payload', async () => {
    getAccessToken.mockReturnValue('tok123');
    const body = {};
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body });
    vi.stubGlobal('fetch', fetchMock);
    const payload = { inn: '7707083893' };

    const result = await ruBusinessCheckApi.startScan(payload);

    expect(fetchMock).toHaveBeenCalledWith(`${baseURL}/api/ru-business-check/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer tok123',
      },
      body: JSON.stringify(payload),
      signal: undefined,
    });
    expect(result).toBe(body);
  });

  it('throws when the response is not ok', async () => {
    getAccessToken.mockReturnValue('tok123');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, statusText: 'Forbidden' }));

    await expect(ruBusinessCheckApi.startScan({ inn: '7707083893' })).rejects.toThrow(
      'Server error: Forbidden'
    );
  });
});

describe('ruBusinessCheckApi.cancelScan', () => {
  it('posts to the cancel endpoint for the given search id', async () => {
    api.post.mockResolvedValue({});

    await ruBusinessCheckApi.cancelScan('search-1');

    expect(api.post).toHaveBeenCalledWith('/api/ru-business-check/history/search-1/cancel');
  });
});

describe('ruBusinessCheckApi.listHistory', () => {
  it('requests paginated history with default skip/limit', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await ruBusinessCheckApi.listHistory();

    expect(api.get).toHaveBeenCalledWith('/api/ru-business-check/history', { params: { skip: 0, limit: 100 } });
    expect(result).toEqual({ items: [] });
  });
});

describe('ruBusinessCheckApi.getHistory', () => {
  it('requests a single history entry by id', async () => {
    api.get.mockResolvedValue({ data: { id: 'search-1' } });

    const result = await ruBusinessCheckApi.getHistory('search-1');

    expect(api.get).toHaveBeenCalledWith('/api/ru-business-check/history/search-1');
    expect(result).toEqual({ id: 'search-1' });
  });
});

describe('ruBusinessCheckApi.deleteHistory', () => {
  it('deletes a history entry by id', async () => {
    api.delete.mockResolvedValue({});

    await ruBusinessCheckApi.deleteHistory('search-1');

    expect(api.delete).toHaveBeenCalledWith('/api/ru-business-check/history/search-1');
  });
});

describe('ruBusinessCheckApi.exportReport', () => {
  it('requests the report as a blob in the given format', async () => {
    const blob = new Blob(['pdf bytes']);
    api.get.mockResolvedValue({ data: blob });

    const result = await ruBusinessCheckApi.exportReport('search-1', 'pdf');

    expect(api.get).toHaveBeenCalledWith('/api/ru-business-check/history/search-1/report', {
      params: { format: 'pdf' },
      responseType: 'blob',
    });
    expect(result).toBe(blob);
  });
});

describe('ruBusinessCheckApi.getConfig', () => {
  it('requests the ru-business-check settings', async () => {
    api.get.mockResolvedValue({ data: { cacheTtlHours: 24 } });

    const result = await ruBusinessCheckApi.getConfig();

    expect(api.get).toHaveBeenCalledWith('/api/settings/ru-business-check');
    expect(result).toEqual({ cacheTtlHours: 24 });
  });
});

describe('ruBusinessCheckApi.updateConfig', () => {
  it('puts the updated config', async () => {
    api.put.mockResolvedValue({ data: { cacheTtlHours: 48 } });

    const result = await ruBusinessCheckApi.updateConfig({ cacheTtlHours: 48 });

    expect(api.put).toHaveBeenCalledWith('/api/settings/ru-business-check', { cacheTtlHours: 48 });
    expect(result).toEqual({ cacheTtlHours: 48 });
  });
});

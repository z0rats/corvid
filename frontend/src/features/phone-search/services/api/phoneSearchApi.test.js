import api from '../../../../core/services/baseApi';
import { phoneSearchApi } from './phoneSearchApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
  baseURL: 'http://backend.test',
}));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('phoneSearchApi.listRuns', () => {
  it('requests paginated runs with default skip/limit', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await phoneSearchApi.listRuns();

    expect(api.get).toHaveBeenCalledWith('/api/phone-search/runs', { params: { skip: 0, limit: 100 } });
    expect(result).toEqual({ items: [] });
  });
});

describe('phoneSearchApi.getRun', () => {
  it('requests a single run by id', async () => {
    api.get.mockResolvedValue({ data: { id: 'search-1' } });

    const result = await phoneSearchApi.getRun('search-1');

    expect(api.get).toHaveBeenCalledWith('/api/phone-search/runs/search-1');
    expect(result).toEqual({ id: 'search-1' });
  });
});

describe('phoneSearchApi.deleteRun', () => {
  it('deletes a run by id', async () => {
    api.delete.mockResolvedValue({});

    await phoneSearchApi.deleteRun('search-1');

    expect(api.delete).toHaveBeenCalledWith('/api/phone-search/runs/search-1');
  });
});

describe('phoneSearchApi.getInfo', () => {
  it('requests checker info', async () => {
    api.get.mockResolvedValue({ data: { provider_count: 3 } });

    const result = await phoneSearchApi.getInfo();

    expect(api.get).toHaveBeenCalledWith('/api/phone-search/info');
    expect(result).toEqual({ provider_count: 3 });
  });
});

describe('phoneSearchApi.getConfig', () => {
  it('requests the phone-search settings', async () => {
    api.get.mockResolvedValue({ data: { timeout_seconds: 10 } });

    const result = await phoneSearchApi.getConfig();

    expect(api.get).toHaveBeenCalledWith('/api/settings/phone-search');
    expect(result).toEqual({ timeout_seconds: 10 });
  });
});

describe('phoneSearchApi.updateConfig', () => {
  it('puts the updated config', async () => {
    api.put.mockResolvedValue({ data: { timeout_seconds: 20 } });

    const result = await phoneSearchApi.updateConfig({ timeout_seconds: 20 });

    expect(api.put).toHaveBeenCalledWith('/api/settings/phone-search', { timeout_seconds: 20 });
    expect(result).toEqual({ timeout_seconds: 20 });
  });
});

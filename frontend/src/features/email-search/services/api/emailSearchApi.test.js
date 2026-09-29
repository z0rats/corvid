import api from '../../../../core/services/baseApi';
import { emailSearchApi } from './emailSearchApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
  baseURL: 'http://backend.test',
}));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('emailSearchApi.listRuns', () => {
  it('requests paginated runs with default skip/limit', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await emailSearchApi.listRuns();

    expect(api.get).toHaveBeenCalledWith('/api/email-search/runs', { params: { skip: 0, limit: 100 } });
    expect(result).toEqual({ items: [] });
  });
});

describe('emailSearchApi.getRun', () => {
  it('requests a single run by id', async () => {
    api.get.mockResolvedValue({ data: { id: 'search-1' } });

    const result = await emailSearchApi.getRun('search-1');

    expect(api.get).toHaveBeenCalledWith('/api/email-search/runs/search-1');
    expect(result).toEqual({ id: 'search-1' });
  });
});

describe('emailSearchApi.deleteRun', () => {
  it('deletes a run by id', async () => {
    api.delete.mockResolvedValue({});

    await emailSearchApi.deleteRun('search-1');

    expect(api.delete).toHaveBeenCalledWith('/api/email-search/runs/search-1');
  });
});

describe('emailSearchApi.getInfo', () => {
  it('requests checker info', async () => {
    api.get.mockResolvedValue({ data: { version: '1.0' } });

    const result = await emailSearchApi.getInfo();

    expect(api.get).toHaveBeenCalledWith('/api/email-search/info');
    expect(result).toEqual({ version: '1.0' });
  });
});

describe('emailSearchApi.checkUpdate', () => {
  it('posts to the check-update endpoint', async () => {
    api.post.mockResolvedValue({ data: { updateAvailable: false } });

    const result = await emailSearchApi.checkUpdate();

    expect(api.post).toHaveBeenCalledWith('/api/email-search/check-update');
    expect(result).toEqual({ updateAvailable: false });
  });
});

describe('emailSearchApi.getConfig', () => {
  it('requests the email-search settings', async () => {
    api.get.mockResolvedValue({ data: { smtpEnabled: false } });

    const result = await emailSearchApi.getConfig();

    expect(api.get).toHaveBeenCalledWith('/api/settings/email-search');
    expect(result).toEqual({ smtpEnabled: false });
  });
});

describe('emailSearchApi.updateConfig', () => {
  it('puts the updated config', async () => {
    api.put.mockResolvedValue({ data: { smtpEnabled: true } });

    const result = await emailSearchApi.updateConfig({ smtpEnabled: true });

    expect(api.put).toHaveBeenCalledWith('/api/settings/email-search', { smtpEnabled: true });
    expect(result).toEqual({ smtpEnabled: true });
  });
});

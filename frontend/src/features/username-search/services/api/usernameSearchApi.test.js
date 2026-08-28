import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';
import { usernameSearchApi } from './usernameSearchApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
  baseURL: 'http://backend.test',
}));
vi.mock('../../../../core/utils/accessToken', () => ({ getAccessToken: vi.fn() }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('usernameSearchApi.startScan', () => {
  it('defaults source to maigret and omits empty tags/excludedTags', async () => {
    getAccessToken.mockReturnValue('tok123');
    const body = {};
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body });
    vi.stubGlobal('fetch', fetchMock);

    const result = await usernameSearchApi.startScan('someuser');

    expect(fetchMock).toHaveBeenCalledWith(`${baseURL}/api/username-search/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer tok123',
      },
      body: JSON.stringify({
        username: 'someuser',
        source: 'maigret',
        tags: undefined,
        excluded_tags: undefined,
      }),
      signal: undefined,
    });
    expect(result).toBe(body);
  });

  it('passes through source, tags, and excludedTags when given', async () => {
    getAccessToken.mockReturnValue('tok123');
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body: {} });
    vi.stubGlobal('fetch', fetchMock);

    await usernameSearchApi.startScan('someuser', {
      source: 'social_analyzer',
      tags: ['social'],
      excludedTags: ['adult'],
    });

    const [, options] = fetchMock.mock.calls[0];
    expect(JSON.parse(options.body)).toEqual({
      username: 'someuser',
      source: 'social_analyzer',
      tags: ['social'],
      excluded_tags: ['adult'],
    });
  });

  it('throws when the response is not ok', async () => {
    getAccessToken.mockReturnValue('tok123');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, statusText: 'Forbidden' }));

    await expect(usernameSearchApi.startScan('someuser')).rejects.toThrow('Server error: Forbidden');
  });
});

describe('usernameSearchApi.cancelScan', () => {
  it('posts to the cancel endpoint for the given search id', async () => {
    api.post.mockResolvedValue({});

    await usernameSearchApi.cancelScan('search-1');

    expect(api.post).toHaveBeenCalledWith('/api/username-search/runs/search-1/cancel');
  });
});

describe('usernameSearchApi.checkHudsonRock', () => {
  it('requests the Hudson Rock status for the given username', async () => {
    api.get.mockResolvedValue({ data: { compromised: false } });

    const result = await usernameSearchApi.checkHudsonRock('someuser');

    expect(api.get).toHaveBeenCalledWith('/api/username-search/hudson-rock', {
      params: { username: 'someuser' },
      signal: undefined,
    });
    expect(result).toEqual({ compromised: false });
  });
});

describe('usernameSearchApi.getTags', () => {
  it('requests the available site tags', async () => {
    api.get.mockResolvedValue({ data: ['social', 'gaming'] });

    const result = await usernameSearchApi.getTags();

    expect(api.get).toHaveBeenCalledWith('/api/username-search/tags');
    expect(result).toEqual(['social', 'gaming']);
  });
});

describe('usernameSearchApi.getInfo', () => {
  it('requests tool version info', async () => {
    api.get.mockResolvedValue({ data: { maigretVersion: '0.5.0' } });

    const result = await usernameSearchApi.getInfo();

    expect(api.get).toHaveBeenCalledWith('/api/username-search/info');
    expect(result).toEqual({ maigretVersion: '0.5.0' });
  });
});

describe('usernameSearchApi.refreshDb', () => {
  it('posts to refresh the site database', async () => {
    api.post.mockResolvedValue({ data: { success: true } });

    const result = await usernameSearchApi.refreshDb();

    expect(api.post).toHaveBeenCalledWith('/api/username-search/refresh-db');
    expect(result).toEqual({ success: true });
  });
});

describe('usernameSearchApi.checkSocialAnalyzerUpdate', () => {
  it('posts to check for a social-analyzer update', async () => {
    api.post.mockResolvedValue({ data: { updateAvailable: false } });

    const result = await usernameSearchApi.checkSocialAnalyzerUpdate();

    expect(api.post).toHaveBeenCalledWith('/api/username-search/social-analyzer/check-update');
    expect(result).toEqual({ updateAvailable: false });
  });
});

describe('usernameSearchApi.checkMaigretUpdate', () => {
  it('posts to check for a maigret update', async () => {
    api.post.mockResolvedValue({ data: { updateAvailable: true } });

    const result = await usernameSearchApi.checkMaigretUpdate();

    expect(api.post).toHaveBeenCalledWith('/api/username-search/maigret/check-update');
    expect(result).toEqual({ updateAvailable: true });
  });
});

describe('usernameSearchApi.listRuns', () => {
  it('requests paginated runs with default skip/limit', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await usernameSearchApi.listRuns();

    expect(api.get).toHaveBeenCalledWith('/api/username-search/runs', { params: { skip: 0, limit: 100 } });
    expect(result).toEqual({ items: [] });
  });
});

describe('usernameSearchApi.getRun', () => {
  it('requests a single run by id', async () => {
    api.get.mockResolvedValue({ data: { id: 'search-1' } });

    const result = await usernameSearchApi.getRun('search-1');

    expect(api.get).toHaveBeenCalledWith('/api/username-search/runs/search-1');
    expect(result).toEqual({ id: 'search-1' });
  });
});

describe('usernameSearchApi.deleteRun', () => {
  it('deletes a run by id', async () => {
    api.delete.mockResolvedValue({});

    await usernameSearchApi.deleteRun('search-1');

    expect(api.delete).toHaveBeenCalledWith('/api/username-search/runs/search-1');
  });
});

describe('usernameSearchApi.exportUrl', () => {
  it('builds the export download URL for the given format', () => {
    const url = usernameSearchApi.exportUrl('search-1', 'pdf');

    expect(url).toBe(`${baseURL}/api/username-search/runs/search-1/export/pdf`);
  });
});

describe('usernameSearchApi.getConfig', () => {
  it('requests the username-search settings', async () => {
    api.get.mockResolvedValue({ data: { source: 'maigret' } });

    const result = await usernameSearchApi.getConfig();

    expect(api.get).toHaveBeenCalledWith('/api/settings/username-search');
    expect(result).toEqual({ source: 'maigret' });
  });
});

describe('usernameSearchApi.updateConfig', () => {
  it('puts the updated config', async () => {
    api.put.mockResolvedValue({ data: { source: 'social_analyzer' } });

    const result = await usernameSearchApi.updateConfig({ source: 'social_analyzer' });

    expect(api.put).toHaveBeenCalledWith('/api/settings/username-search', { source: 'social_analyzer' });
    expect(result).toEqual({ source: 'social_analyzer' });
  });
});

describe('usernameSearchApi.getSocialAnalyzerConfig', () => {
  it('requests the social-analyzer settings', async () => {
    api.get.mockResolvedValue({ data: { watchdogSeconds: 60 } });

    const result = await usernameSearchApi.getSocialAnalyzerConfig();

    expect(api.get).toHaveBeenCalledWith('/api/settings/social-analyzer');
    expect(result).toEqual({ watchdogSeconds: 60 });
  });
});

describe('usernameSearchApi.updateSocialAnalyzerConfig', () => {
  it('puts the updated social-analyzer config', async () => {
    api.put.mockResolvedValue({ data: { watchdogSeconds: 120 } });

    const result = await usernameSearchApi.updateSocialAnalyzerConfig({ watchdogSeconds: 120 });

    expect(api.put).toHaveBeenCalledWith('/api/settings/social-analyzer', { watchdogSeconds: 120 });
    expect(result).toEqual({ watchdogSeconds: 120 });
  });
});

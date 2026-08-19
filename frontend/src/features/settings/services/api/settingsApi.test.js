import api from '../../../../core/services/baseApi';
import { settingsApi } from './settingsApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('settingsApi — general settings', () => {
  it('updateDarkmode puts the flag as a query param', async () => {
    api.put.mockResolvedValue({ data: { darkmode: true } });

    const result = await settingsApi.updateDarkmode(true);

    expect(api.put).toHaveBeenCalledWith('/api/settings/general/darkmode?darkmode=true');
    expect(result).toEqual({ darkmode: true });
  });

  it('updateLanguage puts the language in the body', async () => {
    api.put.mockResolvedValue({ data: { language: 'ru' } });

    const result = await settingsApi.updateLanguage('ru');

    expect(api.put).toHaveBeenCalledWith('/api/settings/general/language', { language: 'ru' });
    expect(result).toEqual({ language: 'ru' });
  });

  it('updateCommandPaletteSettings converts to snake_case fields', async () => {
    api.put.mockResolvedValue({ data: {} });

    await settingsApi.updateCommandPaletteSettings({
      autoOpenOnSingleMatch: true,
      startScreen: 'recent',
      alwaysTiles: false,
    });

    expect(api.put).toHaveBeenCalledWith('/api/settings/general/command-palette', {
      auto_open_on_single_match: true,
      start_screen: 'recent',
      always_tiles: false,
    });
  });
});

describe('settingsApi — api keys', () => {
  it('getServicesConfig fetches the config', async () => {
    api.get.mockResolvedValue({ data: { abuseipdb: {} } });
    const result = await settingsApi.getServicesConfig();
    expect(api.get).toHaveBeenCalledWith('/api/services/config');
    expect(result).toEqual({ abuseipdb: {} });
  });

  it('getConfiguredApiKeys fetches configured keys', async () => {
    api.get.mockResolvedValue({ data: { abuseipdb: true } });
    const result = await settingsApi.getConfiguredApiKeys();
    expect(api.get).toHaveBeenCalledWith('/api/apikeys/configured');
    expect(result).toEqual({ abuseipdb: true });
  });

  it('getActiveApiKeys fetches active keys', async () => {
    api.get.mockResolvedValue({ data: { abuseipdb: true } });
    const result = await settingsApi.getActiveApiKeys();
    expect(api.get).toHaveBeenCalledWith('/api/apikeys/is_active');
    expect(result).toEqual({ abuseipdb: true });
  });

  it('createApiKey posts with defaults for isActive/bulkIocLookup', async () => {
    api.post.mockResolvedValue({ data: {} });

    await settingsApi.createApiKey('abuseipdb', 'secret');

    expect(api.post).toHaveBeenCalledWith('/api/apikeys', {
      name: 'abuseipdb',
      key: 'secret',
      is_active: true,
      bulk_ioc_lookup: false,
    });
  });

  it('createApiKey posts explicit isActive/bulkIocLookup when given', async () => {
    api.post.mockResolvedValue({ data: {} });

    await settingsApi.createApiKey('abuseipdb', 'secret', false, true);

    expect(api.post).toHaveBeenCalledWith('/api/apikeys', {
      name: 'abuseipdb',
      key: 'secret',
      is_active: false,
      bulk_ioc_lookup: true,
    });
  });

  it('updateApiKey patches the named key', async () => {
    api.patch.mockResolvedValue({ data: {} });

    await settingsApi.updateApiKey('abuseipdb', 'new-secret');

    expect(api.patch).toHaveBeenCalledWith('/api/apikeys/abuseipdb', {
      key: 'new-secret',
      is_active: true,
      bulk_ioc_lookup: false,
    });
  });

  it('updateApiKeyStatus patches only the active flag', async () => {
    api.patch.mockResolvedValue({ data: {} });

    await settingsApi.updateApiKeyStatus('abuseipdb', false);

    expect(api.patch).toHaveBeenCalledWith('/api/apikeys/abuseipdb/is_active', { is_active: false });
  });

  it('deleteApiKey deletes the named key', async () => {
    api.delete.mockResolvedValue({ data: {} });

    await settingsApi.deleteApiKey('abuseipdb');

    expect(api.delete).toHaveBeenCalledWith('/api/apikeys/abuseipdb');
  });

  it('getQuotaStatus fetches quota data', async () => {
    api.get.mockResolvedValue({ data: [{ service: 'abuseipdb' }] });
    const result = await settingsApi.getQuotaStatus();
    expect(api.get).toHaveBeenCalledWith('/api/services/quota');
    expect(result).toEqual([{ service: 'abuseipdb' }]);
  });
});

describe('settingsApi — ai settings', () => {
  it('getAiSettings fetches settings', async () => {
    api.get.mockResolvedValue({ data: { defaultModel: 'gpt' } });
    const result = await settingsApi.getAiSettings();
    expect(api.get).toHaveBeenCalledWith('/api/settings/ai');
    expect(result).toEqual({ defaultModel: 'gpt' });
  });

  it('updateAiSettings puts the given settings', async () => {
    api.put.mockResolvedValue({ data: { defaultModel: 'claude' } });
    const result = await settingsApi.updateAiSettings({ defaultModel: 'claude' });
    expect(api.put).toHaveBeenCalledWith('/api/settings/ai', { defaultModel: 'claude' });
    expect(result).toEqual({ defaultModel: 'claude' });
  });

  it('getAvailableModels fetches the model list', async () => {
    api.get.mockResolvedValue({ data: { models: ['gpt-4'] } });
    const result = await settingsApi.getAvailableModels();
    expect(api.get).toHaveBeenCalledWith('/api/settings/ai/available-models');
    expect(result).toEqual({ models: ['gpt-4'] });
  });
});

describe('settingsApi — modules', () => {
  it('updateModuleStatus patches the enabled flag', async () => {
    api.patch.mockResolvedValue({ data: {} });

    await settingsApi.updateModuleStatus('newsfeed', false);

    expect(api.patch).toHaveBeenCalledWith('/api/settings/modules/newsfeed/status', { enabled: false });
  });
});

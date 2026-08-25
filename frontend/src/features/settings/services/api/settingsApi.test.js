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

describe('settingsApi — backup status', () => {
  it('getBackupStatus fetches status', async () => {
    api.get.mockResolvedValue({ data: { supported: true, db_dialect: 'sqlite' } });

    const result = await settingsApi.getBackupStatus();

    expect(api.get).toHaveBeenCalledWith('/api/backup/status');
    expect(result).toEqual({ supported: true, db_dialect: 'sqlite' });
  });
});

describe('settingsApi — exportBackup', () => {
  it('posts snake_case options as a blob request', async () => {
    api.post.mockResolvedValue({ data: new Blob(['x']), headers: {} });

    await settingsApi.exportBackup({ includeAccessToken: true, passphrase: 'hunter2' });

    expect(api.post).toHaveBeenCalledWith(
      '/api/backup/export',
      { include_access_token: true, passphrase: 'hunter2' },
      { responseType: 'blob' }
    );
  });

  it('defaults to no access token and no passphrase', async () => {
    api.post.mockResolvedValue({ data: new Blob(['x']), headers: {} });

    await settingsApi.exportBackup();

    expect(api.post).toHaveBeenCalledWith(
      '/api/backup/export',
      { include_access_token: false, passphrase: null },
      { responseType: 'blob' }
    );
  });

  it('extracts the filename from the content-disposition header', async () => {
    const blob = new Blob(['x']);
    api.post.mockResolvedValue({
      data: blob,
      headers: { 'content-disposition': 'attachment; filename="corvid-backup-x.tar.gz"' },
    });

    const result = await settingsApi.exportBackup();

    expect(result).toEqual({ blob, filename: 'corvid-backup-x.tar.gz' });
  });

  it('falls back to a generic filename with no content-disposition header', async () => {
    api.post.mockResolvedValue({ data: new Blob(['x']), headers: {} });

    const result = await settingsApi.exportBackup();

    expect(result.filename).toBe('corvid-backup.tar.gz');
  });

  it('surfaces the parsed detail message from a blob error response', async () => {
    const errorBlob = new Blob([JSON.stringify({ detail: 'No encryption key file found' })]);
    api.post.mockRejectedValue({ message: 'Request failed', response: { data: errorBlob } });

    await expect(settingsApi.exportBackup()).rejects.toThrow('No encryption key file found');
  });

  it('rethrows the original error when the blob body is not JSON', async () => {
    const originalError = { message: 'Request failed', response: { data: new Blob(['not json']) } };
    api.post.mockRejectedValue(originalError);

    await expect(settingsApi.exportBackup()).rejects.toBe(originalError);
  });

  it('rethrows the original error when there is no response body at all', async () => {
    const originalError = new Error('Network error');
    api.post.mockRejectedValue(originalError);

    await expect(settingsApi.exportBackup()).rejects.toBe(originalError);
  });
});

describe('settingsApi — restoreBackup', () => {
  it('posts a multipart form with the file and confirm phrase', async () => {
    api.post.mockResolvedValue({ data: { restart_required: true, access_token_restored: false } });
    const file = new File(['content'], 'backup.tar.gz');

    const result = await settingsApi.restoreBackup({ file, passphrase: 'hunter2' });

    expect(api.post).toHaveBeenCalledWith('/api/backup/restore', expect.any(FormData), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    const formData = api.post.mock.calls[0][1];
    expect(formData.get('file')).toBe(file);
    expect(formData.get('confirm')).toBe('RESTORE');
    expect(formData.get('passphrase')).toBe('hunter2');
    expect(result).toEqual({ restart_required: true, access_token_restored: false });
  });

  it('omits the passphrase field when none is given', async () => {
    api.post.mockResolvedValue({ data: {} });
    const file = new File(['content'], 'backup.tar.gz');

    await settingsApi.restoreBackup({ file });

    const formData = api.post.mock.calls[0][1];
    expect(formData.has('passphrase')).toBe(false);
  });
});

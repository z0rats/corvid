import api from '../../../../core/services/baseApi';

/**
 * A blob-responseType request still gets its error body as a Blob (axios applies
 * responseType to error responses too), so the JSON `detail`/`error_code` the
 * backend sends has to be read back out of it manually here instead of just
 * surfacing the raw axios error.
 */
async function toApiError(err) {
  const data = err.response?.data;
  if (data instanceof Blob) {
    try {
      const parsed = JSON.parse(await data.text());
      return new Error(parsed.detail || err.message);
    } catch {
      // fall through to the generic axios error below
    }
  }
  return err;
}

export const settingsApi = {
  // General settings API calls
  async updateDarkmode(darkmode) {
    const response = await api.put(`/api/settings/general/darkmode?darkmode=${darkmode}`);
    return response.data;
  },

  async updateLanguage(language) {
    const response = await api.put('/api/settings/general/language', { language });
    return response.data;
  },

  async updateCommandPaletteSettings({ autoOpenOnSingleMatch, startScreen, alwaysTiles }) {
    const response = await api.put('/api/settings/general/command-palette', {
      auto_open_on_single_match: autoOpenOnSingleMatch,
      start_screen: startScreen,
      always_tiles: alwaysTiles,
    });
    return response.data;
  },

  // API Keys API calls
  async getServicesConfig() {
    const response = await api.get('/api/services/config');
    return response.data;
  },

  async getConfiguredApiKeys() {
    const response = await api.get('/api/apikeys/configured');
    return response.data;
  },

  async getActiveApiKeys() {
    const response = await api.get('/api/apikeys/is_active');
    return response.data;
  },

  async createApiKey(name, key, isActive = true, bulkIocLookup = false) {
    const response = await api.post('/api/apikeys', {
      name,
      key,
      is_active: isActive,
      bulk_ioc_lookup: bulkIocLookup,
    });
    return response.data;
  },

  async updateApiKey(name, key, isActive = true, bulkIocLookup = false) {
    const response = await api.patch(`/api/apikeys/${name}`, {
      key,
      is_active: isActive,
      bulk_ioc_lookup: bulkIocLookup,
    });
    return response.data;
  },

  async updateApiKeyStatus(name, isActive) {
    const response = await api.patch(`/api/apikeys/${name}/is_active`, {
      is_active: isActive,
    });
    return response.data;
  },

  async deleteApiKey(name) {
    const response = await api.delete(`/api/apikeys/${name}`);
    return response.data;
  },

  async getQuotaStatus() {
    const response = await api.get('/api/services/quota');
    return response.data;
  },

  // AI Settings API calls
  async getAiSettings() {
    const response = await api.get('/api/settings/ai');
    return response.data;
  },

  async updateAiSettings(settings) {
    const response = await api.put('/api/settings/ai', settings);
    return response.data;
  },

  async getAvailableModels() {
    const response = await api.get('/api/settings/ai/available-models');
    return response.data;
  },

  // Modules API calls
  async updateModuleStatus(moduleName, enabled) {
    const response = await api.patch(`/api/settings/modules/${moduleName}/status`, {
      enabled: enabled
    });
    return response.data;
  },

  // Backup API calls
  async getBackupStatus() {
    const response = await api.get('/api/backup/status');
    return response.data;
  },

  async exportBackup({ includeAccessToken = false, passphrase = null } = {}) {
    // Blob response, same pattern as ru-business-check's report export: a plain
    // <a href> download can't carry the Authorization header this app requires.
    try {
      const response = await api.post(
        '/api/backup/export',
        { include_access_token: includeAccessToken, passphrase: passphrase || null },
        { responseType: 'blob' }
      );
      const disposition = response.headers['content-disposition'] || '';
      const match = disposition.match(/filename="?([^"]+)"?/);
      return { blob: response.data, filename: match ? match[1] : 'corvid-backup.tar.gz' };
    } catch (err) {
      throw await toApiError(err);
    }
  },

  async restoreBackup({ file, passphrase = null }) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('confirm', 'RESTORE');
    if (passphrase) {
      formData.append('passphrase', passphrase);
    }

    const response = await api.post('/api/backup/restore', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

import api from '../../../../core/services/baseApi';

export const settingsApi = {
  // General settings API calls
  async updateFont(font) {
    const response = await api.put(`/api/settings/general/font?font=${font}`);
    return response.data;
  },

  async updateDarkmode(darkmode) {
    const response = await api.put(`/api/settings/general/darkmode?darkmode=${darkmode}`);
    return response.data;
  },

  async updateLanguage(language) {
    const response = await api.put('/api/settings/general/language', { language });
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
};

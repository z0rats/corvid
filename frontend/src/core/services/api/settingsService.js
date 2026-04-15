import api from '../baseApi';

/**
 * Settings API service for managing application settings
 */
export const settingsService = {
  async getApiKeys() {
    const response = await api.get('/api/apikeys/is_active');
    return response.data;
  },

  async getModules() {
    const response = await api.get('/api/settings/modules');
    return response.data;
  },

  async getGeneralSettings() {
    const response = await api.get('/api/settings/general');
    return response.data;
  },

  async getNewsfeedList() {
    const response = await api.get('/api/settings/modules/newsfeed');
    return response.data;
  },

  async getAiSettings() {
    const response = await api.get('/api/settings/ai');
    return response.data;
  },
};

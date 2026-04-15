import api from '../../../../core/services/baseApi';

export const newsfeedSettingsApi = {
  async getConfig() {
    const response = await api.get('/api/settings/newsfeed/config');
    return response.data;
  },

  async updateConfig(config) {
    const response = await api.put('/api/settings/newsfeed/config', config);
    return response.data;
  },

  async getCtiSettings() {
    const response = await api.get('/api/settings/cti');
    return response.data;
  },

  async updateCtiSettings(settings) {
    const response = await api.put('/api/settings/cti', { settings });
    return response.data;
  },

  async getKeywords() {
    const response = await api.get('/api/settings/keywords');
    return response.data;
  },

  async addKeyword(keyword) {
    const response = await api.post('/api/settings/keywords', { keyword });
    return response.data;
  },

  async deleteKeyword(keywordId) {
    await api.delete(`/api/settings/keywords/${keywordId}`);
  },

  async getNewsfeeds() {
    const response = await api.get('/api/settings/modules/newsfeed');
    return response.data;
  },

  async addNewsfeed(feed) {
    const response = await api.post('/api/settings/modules/newsfeed', feed);
    return response.data;
  },

  async deleteNewsfeed(name) {
    await api.delete(`/api/settings/modules/newsfeed?feed_name=${encodeURIComponent(name)}`);
  },

  async enableNewsfeed(name) {
    await api.patch(`/api/settings/modules/newsfeed/${encodeURIComponent(name)}/status`, { enabled: true });
  },

  async disableNewsfeed(name) {
    await api.patch(`/api/settings/modules/newsfeed/${encodeURIComponent(name)}/status`, { enabled: false });
  },

  async validateFeed(feed) {
    const response = await api.post('/api/settings/modules/newsfeed/validation', feed);
    return response.data;
  },

  async uploadFeedIcon(encodedName, formData) {
    const response = await api.put(
      `/api/settings/modules/newsfeed/${encodedName}/icon`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  async deleteFeedIcon(encodedName) {
    const response = await api.delete(`/api/settings/modules/newsfeed/${encodedName}/icon`);
    return response.data;
  },

  async refetchFeedIcon(encodedName) {
    const response = await api.post(`/api/settings/modules/newsfeed/${encodedName}/icon/refetch`);
    return response.data;
  },

  async refetchAllMissingIcons() {
    const response = await api.post('/api/settings/modules/newsfeed/icons/refetch-missing');
    return response.data;
  },

  async getBlacklistEntries(type) {
    const params = type ? `?type=${type}` : '';
    const response = await api.get(`/api/settings/newsfeed/trends-blacklist${params}`);
    return response.data;
  },

  async addBlacklistEntry(value, type) {
    const response = await api.post('/api/settings/newsfeed/trends-blacklist', { value, type });
    return response.data;
  },

  async deleteBlacklistEntry(entryId) {
    await api.delete(`/api/settings/newsfeed/trends-blacklist/${entryId}`);
  },
};

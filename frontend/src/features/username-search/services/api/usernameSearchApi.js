import api, { baseURL } from '../../../../core/services/baseApi';

export const usernameSearchApi = {
  async startScan(username, { source, tags, excludedTags, signal } = {}) {
    const response = await fetch(`${baseURL}/api/username-search/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        username,
        source: source || 'maigret',
        tags: tags && tags.length ? tags : undefined,
        excluded_tags: excludedTags && excludedTags.length ? excludedTags : undefined,
      }),
      signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`Server error: ${response.statusText}`);
    }

    return response.body;
  },

  async cancelScan(searchId) {
    await api.post(`/api/username-search/runs/${searchId}/cancel`);
  },

  async getTags() {
    const response = await api.get('/api/username-search/tags');
    return response.data;
  },

  async getInfo() {
    const response = await api.get('/api/username-search/info');
    return response.data;
  },

  async refreshDb() {
    const response = await api.post('/api/username-search/refresh-db');
    return response.data;
  },

  async checkSocialAnalyzerUpdate() {
    const response = await api.post('/api/username-search/social-analyzer/check-update');
    return response.data;
  },

  async checkMaigretUpdate() {
    const response = await api.post('/api/username-search/maigret/check-update');
    return response.data;
  },

  async listRuns(skip = 0, limit = 100) {
    const response = await api.get('/api/username-search/runs', { params: { skip, limit } });
    return response.data;
  },

  async getRun(searchId) {
    const response = await api.get(`/api/username-search/runs/${searchId}`);
    return response.data;
  },

  async deleteRun(searchId) {
    await api.delete(`/api/username-search/runs/${searchId}`);
  },

  exportUrl(searchId, format) {
    return `${baseURL}/api/username-search/runs/${searchId}/export/${format}`;
  },

  async getConfig() {
    const response = await api.get('/api/settings/username-search');
    return response.data;
  },

  async updateConfig(config) {
    const response = await api.put('/api/settings/username-search', config);
    return response.data;
  },

  async getSocialAnalyzerConfig() {
    const response = await api.get('/api/settings/social-analyzer');
    return response.data;
  },

  async updateSocialAnalyzerConfig(config) {
    const response = await api.put('/api/settings/social-analyzer', config);
    return response.data;
  },
};

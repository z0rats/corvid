import api, { baseURL } from '../../../../core/services/baseApi';

export const emailSearchApi = {
  async startScan(username, { signal } = {}) {
    const response = await fetch(`${baseURL}/api/email-search/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({ username }),
      signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`Server error: ${response.statusText}`);
    }

    return response.body;
  },

  async cancelScan(searchId) {
    await api.post(`/api/email-search/runs/${searchId}/cancel`);
  },

  async listRuns(skip = 0, limit = 100) {
    const response = await api.get('/api/email-search/runs', { params: { skip, limit } });
    return response.data;
  },

  async getRun(searchId) {
    const response = await api.get(`/api/email-search/runs/${searchId}`);
    return response.data;
  },

  async deleteRun(searchId) {
    await api.delete(`/api/email-search/runs/${searchId}`);
  },

  async getInfo() {
    const response = await api.get('/api/email-search/info');
    return response.data;
  },

  async checkUpdate() {
    const response = await api.post('/api/email-search/check-update');
    return response.data;
  },

  async getConfig() {
    const response = await api.get('/api/settings/email-search');
    return response.data;
  },

  async updateConfig(config) {
    const response = await api.put('/api/settings/email-search', config);
    return response.data;
  },
};

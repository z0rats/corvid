import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';

export const phoneSearchApi = {
  async startScan(phoneNumber, { signal } = {}) {
    const response = await fetch(`${baseURL}/api/phone-search/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': `Bearer ${getAccessToken()}`,
      },
      body: JSON.stringify({ phone_number: phoneNumber }),
      signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`Server error: ${response.statusText}`);
    }

    return response.body;
  },

  async cancelScan(searchId) {
    await api.post(`/api/phone-search/runs/${searchId}/cancel`);
  },

  async listRuns(skip = 0, limit = 100) {
    const response = await api.get('/api/phone-search/runs', { params: { skip, limit } });
    return response.data;
  },

  async getRun(searchId) {
    const response = await api.get(`/api/phone-search/runs/${searchId}`);
    return response.data;
  },

  async deleteRun(searchId) {
    await api.delete(`/api/phone-search/runs/${searchId}`);
  },

  async getInfo() {
    const response = await api.get('/api/phone-search/info');
    return response.data;
  },

  async getConfig() {
    const response = await api.get('/api/settings/phone-search');
    return response.data;
  },

  async updateConfig(config) {
    const response = await api.put('/api/settings/phone-search', config);
    return response.data;
  },
};

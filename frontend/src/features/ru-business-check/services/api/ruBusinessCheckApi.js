import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';

export const ruBusinessCheckApi = {
  async startScan(payload, { signal } = {}) {
    const response = await fetch(`${baseURL}/api/ru-business-check/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': `Bearer ${getAccessToken()}`,
      },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`Server error: ${response.statusText}`);
    }

    return response.body;
  },

  async cancelScan(searchId) {
    await api.post(`/api/ru-business-check/history/${searchId}/cancel`);
  },

  async listHistory(skip = 0, limit = 100) {
    const response = await api.get('/api/ru-business-check/history', { params: { skip, limit } });
    return response.data;
  },

  async getHistory(searchId) {
    const response = await api.get(`/api/ru-business-check/history/${searchId}`);
    return response.data;
  },

  async deleteHistory(searchId) {
    await api.delete(`/api/ru-business-check/history/${searchId}`);
  },

  async exportReport(searchId, format) {
    // A plain `<a href>` download can't carry the Authorization header this app requires
    // on every /api/* request, so this goes through the authenticated axios instance as a
    // blob instead - same pattern as email_analyzer's exportReport.
    const response = await api.get(`/api/ru-business-check/history/${searchId}/report`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },

  async getConfig() {
    const response = await api.get('/api/settings/ru-business-check');
    return response.data;
  },

  async updateConfig(config) {
    const response = await api.put('/api/settings/ru-business-check', config);
    return response.data;
  },
};

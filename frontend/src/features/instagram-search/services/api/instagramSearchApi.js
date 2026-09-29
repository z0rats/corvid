import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';

export const instagramSearchApi = {
  async lookupProfile(username) {
    const response = await api.post('/api/instagram-search/profile', { username });
    return response.data;
  },

  async getHealth() {
    const response = await api.get('/api/instagram-search/health');
    return response.data;
  },

  async startScan({ username, scanType }, { signal } = {}) {
    const response = await fetch(`${baseURL}/api/instagram-search/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        Authorization: `Bearer ${getAccessToken()}`,
      },
      body: JSON.stringify({ username, scan_type: scanType }),
      signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`Server error: ${response.statusText}`);
    }

    return response.body;
  },

  async cancelScan(searchId) {
    await api.post(`/api/instagram-search/history/${searchId}/cancel`);
  },

  async listHistory(skip = 0, limit = 100) {
    const response = await api.get('/api/instagram-search/history', { params: { skip, limit } });
    return response.data;
  },

  async getHistory(searchId) {
    const response = await api.get(`/api/instagram-search/history/${searchId}`);
    return response.data;
  },

  async deleteHistory(searchId) {
    await api.delete(`/api/instagram-search/history/${searchId}`);
  },
};

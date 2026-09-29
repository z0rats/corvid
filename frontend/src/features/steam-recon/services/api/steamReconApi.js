import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';

export const steamReconApi = {
  async profile(target) {
    const response = await api.post('/api/steam-recon/profile', { target });
    return response.data;
  },

  async startScan({ target, maxFriends, includeCsReport }, { signal } = {}) {
    const response = await fetch(`${baseURL}/api/steam-recon/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        Authorization: `Bearer ${getAccessToken()}`,
      },
      body: JSON.stringify({
        target,
        max_friends: maxFriends,
        include_cs_report: includeCsReport,
      }),
      signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`Server error: ${response.statusText}`);
    }

    return response.body;
  },

  async cancelScan(searchId) {
    await api.post(`/api/steam-recon/history/${searchId}/cancel`);
  },

  async listSearches(skip = 0, limit = 100) {
    const response = await api.get('/api/steam-recon/history', { params: { skip, limit } });
    return response.data;
  },

  async getSearch(searchId) {
    const response = await api.get(`/api/steam-recon/history/${searchId}`);
    return response.data;
  },

  async deleteSearch(searchId) {
    await api.delete(`/api/steam-recon/history/${searchId}`);
  },
};

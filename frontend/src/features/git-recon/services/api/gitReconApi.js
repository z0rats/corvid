import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';

export const gitReconApi = {
  async startScan(payload, { signal } = {}) {
    const response = await fetch(`${baseURL}/api/git-recon/scan`, {
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

  async listHistory(skip = 0, limit = 100) {
    const response = await api.get('/api/git-recon/history', { params: { skip, limit } });
    return response.data;
  },

  async getHistory(searchId) {
    const response = await api.get(`/api/git-recon/history/${searchId}`);
    return response.data;
  },

  async deleteHistory(searchId) {
    await api.delete(`/api/git-recon/history/${searchId}`);
  },
};

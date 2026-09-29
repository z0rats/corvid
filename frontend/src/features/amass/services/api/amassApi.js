import api, { baseURL } from '../../../../core/services/baseApi';
import { getAccessToken } from '../../../../core/utils/accessToken';

export const amassApi = {
  async startScan(payload, { signal } = {}) {
    const response = await fetch(`${baseURL}/api/amass/scan`, {
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
    await api.post(`/api/amass/history/${searchId}/cancel`);
  },
  async listHistory(skip = 0, limit = 100) {
    const response = await api.get('/api/amass/history', { params: { skip, limit } });
    return response.data;
  },
  async getHistory(searchId) {
    const response = await api.get(`/api/amass/history/${searchId}`);
    return response.data;
  },
  async deleteHistory(searchId) {
    await api.delete(`/api/amass/history/${searchId}`);
  },
};

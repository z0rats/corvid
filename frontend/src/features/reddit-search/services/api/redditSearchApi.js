import api from '../../../../core/services/baseApi';

export const redditSearchApi = {
  async scan(payload) {
    const response = await api.post('/api/reddit-search/scan', payload);
    return response.data;
  },

  async listHistory(skip = 0, limit = 100) {
    const response = await api.get('/api/reddit-search/history', { params: { skip, limit } });
    return response.data;
  },

  async getHistory(searchId) {
    const response = await api.get(`/api/reddit-search/history/${searchId}`);
    return response.data;
  },

  async deleteHistory(searchId) {
    await api.delete(`/api/reddit-search/history/${searchId}`);
  },
};

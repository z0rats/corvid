import api from '../../../../core/services/baseApi';

export const instagramSearchApi = {
  async lookupProfile(username) {
    const response = await api.post('/api/instagram-search/profile', { username });
    return response.data;
  },

  async getHealth() {
    const response = await api.get('/api/instagram-search/health');
    return response.data;
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

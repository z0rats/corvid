import api from '../../../../core/services/baseApi';

export const steamReconApi = {
  async profile(target) {
    const response = await api.post('/api/steam-recon/profile', { target });
    return response.data;
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

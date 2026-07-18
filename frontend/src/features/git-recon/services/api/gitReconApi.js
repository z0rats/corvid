import api from '../../../../core/services/baseApi';

export const gitReconApi = {
  async scan(payload) {
    const response = await api.post('/api/git-recon/scan', payload);
    return response.data;
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

import api from '../../../../core/services/baseApi';

export const amassApi = {
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

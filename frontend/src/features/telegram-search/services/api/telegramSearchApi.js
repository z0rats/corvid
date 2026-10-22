import api from '../../../../core/services/baseApi';

export const telegramSearchApi = {
  async listSearches(skip = 0, limit = 100) {
    const response = await api.get('/api/telegram-search/history', { params: { skip, limit } });
    return response.data;
  },

  async getSearch(searchId) {
    const response = await api.get(`/api/telegram-search/history/${searchId}`);
    return response.data;
  },

  async deleteSearch(searchId) {
    await api.delete(`/api/telegram-search/history/${searchId}`);
  },
};

import api, { baseURL } from '../../../../../../core/services/baseApi';

export const lookupHistoryApi = {
  async saveSearch(ioc, iocType, results) {
    const response = await api.post('/api/ioc-lookup/history', { ioc, ioc_type: iocType, results });
    return response.data;
  },

  async listSearches(skip = 0, limit = 100) {
    const response = await api.get('/api/ioc-lookup/history', { params: { skip, limit } });
    return response.data;
  },

  async getSearch(searchId) {
    const response = await api.get(`/api/ioc-lookup/history/${searchId}`);
    return response.data;
  },

  async deleteSearch(searchId) {
    await api.delete(`/api/ioc-lookup/history/${searchId}`);
  },

  reportUrl(searchId, format, locale) {
    return `${baseURL}/api/ioc-lookup/history/${searchId}/report?format=${format}&locale=${locale}`;
  },
};

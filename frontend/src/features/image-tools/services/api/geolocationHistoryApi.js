import api, { baseURL } from '../../../../core/services/baseApi';

export const geolocationHistoryApi = {
  async listSearches(skip = 0, limit = 100) {
    const response = await api.get('/api/image/geolocate/history', { params: { skip, limit } });
    return response.data;
  },

  async getSearch(searchId) {
    const response = await api.get(`/api/image/geolocate/history/${searchId}`);
    return response.data;
  },

  async deleteSearch(searchId) {
    await api.delete(`/api/image/geolocate/history/${searchId}`);
  },

  reportUrl(searchId, format) {
    return `${baseURL}/api/image/geolocate/history/${searchId}/report?format=${format}`;
  },
};

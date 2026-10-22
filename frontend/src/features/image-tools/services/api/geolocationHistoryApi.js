import api from '../../../../core/services/baseApi';

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

  /** For core's ApiDownloadButtons, which downloads it through the authenticated client. */
  reportRequest(searchId, format) {
    return {
      path: `/api/image/geolocate/history/${searchId}/report`,
      params: { format },
      fallbackName: `image-geolocation-${searchId}.${format}`,
    };
  },
};

import api from '../../../../core/services/baseApi';

export const streetViewApi = {
  async getKey() {
    const response = await api.get('/api/image/street-view-key');
    return response.data;
  },
};

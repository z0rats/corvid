import api from '../../../../core/services/baseApi';

export const sanctionsSearchApi = {
  async search({ query, schema, limit }) {
    const response = await api.get('/api/sanctions-search/search', {
      params: { q: query, schema, limit },
    });
    return response.data;
  },

  async getSchemas() {
    const response = await api.get('/api/sanctions-search/schemas');
    return response.data;
  },
};

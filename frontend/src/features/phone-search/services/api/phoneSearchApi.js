import api from '../../../../core/services/baseApi';

export const phoneSearchApi = {
  async listRuns(skip = 0, limit = 100) {
    const response = await api.get('/api/phone-search/runs', { params: { skip, limit } });
    return response.data;
  },

  async getRun(searchId) {
    const response = await api.get(`/api/phone-search/runs/${searchId}`);
    return response.data;
  },

  async deleteRun(searchId) {
    await api.delete(`/api/phone-search/runs/${searchId}`);
  },

  async getInfo() {
    const response = await api.get('/api/phone-search/info');
    return response.data;
  },

  async getConfig() {
    const response = await api.get('/api/settings/phone-search');
    return response.data;
  },

  async updateConfig(config) {
    const response = await api.put('/api/settings/phone-search', config);
    return response.data;
  },
};

import api from '../../../../core/services/baseApi';

export const ghuntProfileApi = {
  async lookup(email) {
    const response = await api.post('/api/email-search/ghunt-profile', { email });
    return response.data;
  },

  async getHealth() {
    const response = await api.get('/api/email-search/ghunt-profile/health');
    return response.data;
  },
};

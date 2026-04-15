import api from '../../../../../core/services/baseApi';

export const domainMonitoringApi = {
  async searchDomains(domain) {
    const response = await api.get(`/api/domain/lookup/${domain}`);
    return response.data;
  },

  async searchDomainsPost(domain) {
    // Alternative POST endpoint for domain lookup
    const response = await api.post('/api/domain/lookup', { domain });
    return response.data;
  },

  async checkHealth() {
    const response = await api.get('/api/domain/health');
    return response.data;
  }
};

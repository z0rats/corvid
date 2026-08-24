import api from '../../../../../core/services/baseApi';

export const webCheckApi = {
  async getSslInfo(domain) {
    const response = await api.get(`/api/domain/ssl-info/${domain}`);
    return response.data;
  },
  async getSecurityHeaders(domain) {
    const response = await api.get(`/api/domain/security-headers/${domain}`);
    return response.data;
  },
  async getDnssec(domain) {
    const response = await api.get(`/api/domain/dnssec/${domain}`);
    return response.data;
  },
  async getBlocklist(domain) {
    const response = await api.get(`/api/domain/blocklist/${domain}`);
    return response.data;
  }
};

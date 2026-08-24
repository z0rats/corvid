import api from '../../../../../core/services/baseApi';

export const rapidDnsApi = {
  async lookupRapidDnsSubdomains(domain) {
    const response = await api.get(`/api/domain/rapiddns-subdomains/${domain}`);
    return response.data;
  }
};

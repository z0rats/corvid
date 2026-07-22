import api from '../../../../../core/services/baseApi';

export const dnsLookupApi = {
  async lookupDns(domain) {
    const response = await api.get(`/api/domain/dns/${domain}`);
    return response.data;
  }
};

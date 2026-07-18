import api from '../../../../../core/services/baseApi';

export const whoisLookupApi = {
  async lookupWhois(domain) {
    const response = await api.get(`/api/domain/whois/${domain}`);
    return response.data;
  }
};

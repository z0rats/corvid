import api from '../../../../../core/services/baseApi';

export const dnsDumpsterApi = {
  async lookupDnsDumpster(domain) {
    const response = await api.get(`/api/domain/dnsdumpster/${domain}`);
    return response.data;
  }
};

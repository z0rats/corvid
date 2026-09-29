import api from '../../../../../core/services/baseApi';

export const subfinderApi = {
  async lookupSubfinderSubdomains(domain) {
    const response = await api.get(`/api/domain/subfinder-subdomains/${domain}`);
    return response.data;
  }
};

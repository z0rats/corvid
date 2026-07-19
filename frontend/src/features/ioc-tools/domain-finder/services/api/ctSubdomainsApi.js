import api from '../../../../../core/services/baseApi';

export const ctSubdomainsApi = {
  async lookupCtSubdomains(domain) {
    const response = await api.get(`/api/domain/ct-subdomains/${domain}`);
    return response.data;
  }
};

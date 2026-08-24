import api from '../../../../../core/services/baseApi';

export const hackertargetApi = {
  async lookupHackertargetSubdomains(domain) {
    const response = await api.get(`/api/domain/hackertarget-subdomains/${domain}`);
    return response.data;
  }
};

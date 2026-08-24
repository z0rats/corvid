import api from '../../../../../core/services/baseApi';

export const waybackApi = {
  async lookupWayback(domain, path) {
    const response = await api.get(`/api/domain/wayback/${domain}`, {
      params: path ? { path } : undefined
    });
    return response.data;
  }
};

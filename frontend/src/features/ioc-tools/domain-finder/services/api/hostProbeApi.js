import api from '../../../../../core/services/baseApi';

export const hostProbeApi = {
  async probeHost(domain) {
    const response = await api.get(`/api/domain/host-probe/${domain}`);
    return response.data;
  }
};

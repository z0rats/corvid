import api from '../../../../core/services/baseApi';

export const trendsApi = {
  async getTitleWordFrequency(limit, timeRange) {
    const response = await api.get(`/api/newsfeed/words/top?limit=${limit}&time_range=${timeRange}`);
    return response.data;
  },

  async getTopIocs(iocType, limit, timeRange) {
    const response = await api.get(`/api/newsfeed/iocs/top?ioc_type=${iocType}&limit=${limit}&time_range=${timeRange}`);
    return response.data;
  },

  async getTopCves(limit, timeRange) {
    const response = await api.get(`/api/newsfeed/cves/top?limit=${limit}&time_range=${timeRange}`);
    return response.data;
  },

  async getIocTypeDistribution(timeRange) {
    const response = await api.get(`/api/newsfeed/iocs/distribution?time_range=${timeRange}`);
    return response.data;
  }
};

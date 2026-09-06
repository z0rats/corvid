import api from '../../../../../core/services/baseApi';

export const temporalAnalysisApi = {
  async lookupTemporalAnalysis(domain) {
    const response = await api.get(`/api/domain/temporal-analysis/${domain}`);
    return response.data;
  }
};

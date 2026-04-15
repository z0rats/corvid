import api from '../../../../core/services/baseApi';

export const aiAssistantApi = {
  async analyzeMailBody(input) {
    const response = await api.post('/api/email/ai-analysis', { input });
    return response.data.analysis_result;
  }
};

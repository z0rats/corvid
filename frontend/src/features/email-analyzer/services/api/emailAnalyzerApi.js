import api from '../../../../core/services/baseApi';

export const emailAnalyzerApi = {
  async analyzeEmail(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };
    
    const response = await api.post('/api/email/analyze', formData, config);
    return response.data;
  },

  async exportReport(result, format, locale) {
    const response = await api.post('/api/email/report', result, {
      params: { format, locale },
      responseType: 'blob',
    });
    return response.data;
  },
};

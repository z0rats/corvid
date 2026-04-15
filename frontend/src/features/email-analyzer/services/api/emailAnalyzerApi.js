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
  }
};

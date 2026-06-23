import api from '../../../../core/services/baseApi';

export const imageAnalyzerApi = {
  async analyzeImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };

    const response = await api.post('/api/image/analyze', formData, config);
    return response.data;
  }
};

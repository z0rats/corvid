import api from '../../../../core/services/baseApi';

export const imageAnomalyApi = {
  async analyzeAnomalies(file) {
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };

    const response = await api.post('/api/image/anomalies', formData, config);
    return response.data;
  }
};

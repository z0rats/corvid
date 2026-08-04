import api from '../../../../core/services/baseApi';

export const imageVisualAnalysisApi = {
  async analyzeVisuals(file) {
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };

    const response = await api.post('/api/image/visual-analysis', formData, config);
    return response.data;
  }
};

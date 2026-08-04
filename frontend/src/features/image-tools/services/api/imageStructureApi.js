import api from '../../../../core/services/baseApi';

export const imageStructureApi = {
  async analyzeStructure(file) {
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };

    const response = await api.post('/api/image/structure', formData, config);
    return response.data;
  }
};

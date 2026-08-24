import api from '../../../../core/services/baseApi';

export const chronoverifyApi = {
  async checkProvenance(file) {
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };

    const response = await api.post('/api/image/chronoverify', formData, config);
    return response.data;
  }
};

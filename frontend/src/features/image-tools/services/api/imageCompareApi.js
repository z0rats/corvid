import api from '../../../../core/services/baseApi';

export const imageCompareApi = {
  async compareImages(fileLeft, fileRight) {
    const formData = new FormData();
    formData.append('file_left', fileLeft);
    formData.append('file_right', fileRight);

    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };

    const response = await api.post('/api/image/compare', formData, config);
    return response.data;
  }
};

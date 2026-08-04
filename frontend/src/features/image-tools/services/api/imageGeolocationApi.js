import api from '../../../../core/services/baseApi';

export const imageGeolocationApi = {
  async geolocateImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };

    const response = await api.post('/api/image/geolocate', formData, config);
    return response.data;
  }
};

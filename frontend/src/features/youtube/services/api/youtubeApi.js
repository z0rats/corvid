import api from '../../../../core/services/baseApi';

export const youtubeApi = {
  async lookup(url) {
    const response = await api.post('/api/youtube/lookup', { url });
    return response.data;
  },
};

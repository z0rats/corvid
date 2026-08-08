import api from '../../../../core/services/baseApi';

export const youtubeApi = {
  async lookup(url) {
    const response = await api.post('/api/youtube/lookup', { url });
    return response.data;
  },

  async comments({ url, query, order, pageToken }) {
    const response = await api.post('/api/youtube/comments', {
      url,
      query: query || undefined,
      order,
      page_token: pageToken || undefined,
    });
    return response.data;
  },
};

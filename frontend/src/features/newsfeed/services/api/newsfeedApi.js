import api from '../../../../core/services/baseApi';

export const newsfeedApi = {
  async getArticles(params) {
    const cleanParams = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== null && v !== undefined && v !== '')
    );
    const response = await api.get('/api/newsfeed/articles', { params: cleanParams });
    return response.data;
  },

  async getArticlesByIds(articleIds) {
    const response = await api.post('/api/newsfeed/articles/bulk', { article_ids: articleIds });
    return response.data;
  },

  async updateArticle(articleId, data) {
    const response = await api.patch(`/api/newsfeed/article/${articleId}`, data);
    return response.data;
  },

  async analyzeArticle(articleId, force = false) {
    const response = await api.post(`/api/newsfeed/analyze/${articleId}`, { force });
    return response.data;
  },

  async fetchAndGetNews() {
    const response = await api.post('/api/newsfeed/fetch_and_get');
    return response.data;
  },

  async getRecentArticles(timeFilter) {
    const response = await api.get(`/api/newsfeed/articles/recent?time_filter=${timeFilter}`);
    return response.data;
  },
};

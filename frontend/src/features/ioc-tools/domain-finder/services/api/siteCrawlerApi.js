import api from '../../../../../core/services/baseApi';

export const siteCrawlerApi = {
  async crawlSite(domain) {
    const response = await api.get(`/api/domain/site-crawl/${domain}`);
    return response.data;
  }
};

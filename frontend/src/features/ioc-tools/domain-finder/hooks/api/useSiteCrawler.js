import { useState } from 'react';
import { siteCrawlerApi } from '../../services/api/siteCrawlerApi';

export function useSiteCrawler(domain) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const crawl = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await siteCrawlerApi.crawlSite(domain);
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || err.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, crawl };
}

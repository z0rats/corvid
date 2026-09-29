import api from '../../../../../core/services/baseApi';
import { siteCrawlerApi } from './siteCrawlerApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('siteCrawlerApi.crawlSite', () => {
  it('requests a site crawl for the given domain', async () => {
    api.get.mockResolvedValue({ data: { total_pages_crawled: 1 } });

    const result = await siteCrawlerApi.crawlSite('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/site-crawl/example.com');
    expect(result).toEqual({ total_pages_crawled: 1 });
  });
});

import { act, renderHook, waitFor } from '@testing-library/react';
import { useSiteCrawler } from './useSiteCrawler';
import { siteCrawlerApi } from '../../services/api/siteCrawlerApi';

vi.mock('../../services/api/siteCrawlerApi');

describe('useSiteCrawler', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no data and no error', () => {
    const { result } = renderHook(() => useSiteCrawler('example.com'));

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('populates data on a successful crawl', async () => {
    const mockResult = { domain: 'example.com', total_pages_crawled: 3 };
    siteCrawlerApi.crawlSite.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useSiteCrawler('example.com'));

    await act(async () => {
      await result.current.crawl();
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(mockResult);
    expect(result.current.error).toBeNull();
    expect(siteCrawlerApi.crawlSite).toHaveBeenCalledWith('example.com');
  });

  it('surfaces the API error message on failure', async () => {
    siteCrawlerApi.crawlSite.mockRejectedValue({
      response: { data: { detail: 'Timeout while connecting' } },
    });

    const { result } = renderHook(() => useSiteCrawler('example.com'));

    await act(async () => {
      await result.current.crawl();
    });

    expect(result.current.error).toBe('Timeout while connecting');
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});

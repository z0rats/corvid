import api from '../../../../core/services/baseApi';
import { youtubeApi } from './youtubeApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('youtubeApi.lookup', () => {
  it('posts the video URL', async () => {
    api.post.mockResolvedValue({ data: { title: 'A video' } });

    const result = await youtubeApi.lookup('https://youtu.be/abc123');

    expect(api.post).toHaveBeenCalledWith('/api/youtube/lookup', { url: 'https://youtu.be/abc123' });
    expect(result).toEqual({ title: 'A video' });
  });
});

describe('youtubeApi.comments', () => {
  it('omits empty query/pageToken', async () => {
    api.post.mockResolvedValue({ data: { comments: [] } });

    const result = await youtubeApi.comments({ url: 'https://youtu.be/abc123', order: 'relevance' });

    expect(api.post).toHaveBeenCalledWith('/api/youtube/comments', {
      url: 'https://youtu.be/abc123',
      query: undefined,
      order: 'relevance',
      page_token: undefined,
    });
    expect(result).toEqual({ comments: [] });
  });

  it('passes through query and pageToken when given', async () => {
    api.post.mockResolvedValue({ data: { comments: [] } });

    await youtubeApi.comments({
      url: 'https://youtu.be/abc123',
      query: 'great video',
      order: 'time',
      pageToken: 'next-page',
    });

    expect(api.post).toHaveBeenCalledWith('/api/youtube/comments', {
      url: 'https://youtu.be/abc123',
      query: 'great video',
      order: 'time',
      page_token: 'next-page',
    });
  });
});

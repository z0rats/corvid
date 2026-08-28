import api from '../../../../core/services/baseApi';
import { chronoverifyApi } from './chronoverifyApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('chronoverifyApi.checkProvenance', () => {
  it('posts the file as multipart form data', async () => {
    api.post.mockResolvedValue({ data: { verdict: 'authentic' } });
    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' });

    const result = await chronoverifyApi.checkProvenance(file);

    expect(api.post).toHaveBeenCalledWith(
      '/api/image/chronoverify',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    const formData = api.post.mock.calls[0][1];
    expect(formData.get('file')).toBe(file);
    expect(result).toEqual({ verdict: 'authentic' });
  });
});

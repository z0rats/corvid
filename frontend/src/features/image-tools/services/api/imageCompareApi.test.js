import api from '../../../../core/services/baseApi';
import { imageCompareApi } from './imageCompareApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('imageCompareApi.compareImages', () => {
  it('posts both files as multipart form data', async () => {
    api.post.mockResolvedValue({ data: { similarity: 0.98 } });
    const fileLeft = new File(['left'], 'left.jpg', { type: 'image/jpeg' });
    const fileRight = new File(['right'], 'right.jpg', { type: 'image/jpeg' });

    const result = await imageCompareApi.compareImages(fileLeft, fileRight);

    expect(api.post).toHaveBeenCalledWith(
      '/api/image/compare',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    const formData = api.post.mock.calls[0][1];
    expect(formData.get('file_left')).toBe(fileLeft);
    expect(formData.get('file_right')).toBe(fileRight);
    expect(result).toEqual({ similarity: 0.98 });
  });
});

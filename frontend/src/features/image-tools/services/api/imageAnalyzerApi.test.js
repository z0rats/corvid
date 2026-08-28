import api from '../../../../core/services/baseApi';
import { imageAnalyzerApi } from './imageAnalyzerApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('imageAnalyzerApi.analyzeImage', () => {
  it('posts the file as multipart form data', async () => {
    api.post.mockResolvedValue({ data: { exif: {} } });
    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' });

    const result = await imageAnalyzerApi.analyzeImage(file);

    expect(api.post).toHaveBeenCalledWith(
      '/api/image/analyze',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    const formData = api.post.mock.calls[0][1];
    expect(formData.get('file')).toBe(file);
    expect(result).toEqual({ exif: {} });
  });
});

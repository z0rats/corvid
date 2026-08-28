import api from '../../../../core/services/baseApi';
import { imageAnomalyApi } from './imageAnomalyApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('imageAnomalyApi.analyzeAnomalies', () => {
  it('posts the file as multipart form data', async () => {
    api.post.mockResolvedValue({ data: { anomalies: [] } });
    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' });

    const result = await imageAnomalyApi.analyzeAnomalies(file);

    expect(api.post).toHaveBeenCalledWith(
      '/api/image/anomalies',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    const formData = api.post.mock.calls[0][1];
    expect(formData.get('file')).toBe(file);
    expect(result).toEqual({ anomalies: [] });
  });
});

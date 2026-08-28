import api from '../../../../core/services/baseApi';
import { imageGeolocationApi } from './imageGeolocationApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('imageGeolocationApi.geolocateImage', () => {
  it('posts the file as multipart form data', async () => {
    api.post.mockResolvedValue({ data: { hypotheses: [] } });
    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' });

    const result = await imageGeolocationApi.geolocateImage(file);

    expect(api.post).toHaveBeenCalledWith(
      '/api/image/geolocate',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    const formData = api.post.mock.calls[0][1];
    expect(formData.get('file')).toBe(file);
    expect(result).toEqual({ hypotheses: [] });
  });
});

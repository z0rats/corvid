import api from '../../../../core/services/baseApi';
import { imageMetadataRemovalApi } from './imageMetadataRemovalApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('imageMetadataRemovalApi.removeMetadata', () => {
  it('posts the file with the mode as a query param and requests a blob response', async () => {
    const blob = new Blob(['stripped']);
    api.post.mockResolvedValue({
      data: blob,
      headers: { 'content-disposition': 'attachment; filename="clean.jpg"' },
    });
    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' });

    const result = await imageMetadataRemovalApi.removeMetadata(file, 'all');

    expect(api.post).toHaveBeenCalledWith(
      '/api/image/strip-metadata',
      expect.any(FormData),
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: { mode: 'all' },
        responseType: 'blob',
      }
    );
    const formData = api.post.mock.calls[0][1];
    expect(formData.get('file')).toBe(file);
    expect(result).toEqual({ blob, filename: 'clean.jpg' });
  });

  it('falls back to the original filename when no content-disposition header is present', async () => {
    const blob = new Blob(['stripped']);
    api.post.mockResolvedValue({ data: blob, headers: {} });
    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' });

    const result = await imageMetadataRemovalApi.removeMetadata(file, 'gps');

    expect(result).toEqual({ blob, filename: 'photo.jpg' });
  });
});

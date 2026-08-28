import api from '../../../../core/services/baseApi';
import { imageStructureApi } from './imageStructureApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('imageStructureApi.analyzeStructure', () => {
  it('posts the file as multipart form data', async () => {
    api.post.mockResolvedValue({ data: { blocks: [] } });
    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' });

    const result = await imageStructureApi.analyzeStructure(file);

    expect(api.post).toHaveBeenCalledWith(
      '/api/image/structure',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    const formData = api.post.mock.calls[0][1];
    expect(formData.get('file')).toBe(file);
    expect(result).toEqual({ blocks: [] });
  });
});

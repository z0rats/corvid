import api from '../../../../core/services/baseApi';
import { imageVisualAnalysisApi } from './imageVisualAnalysisApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('imageVisualAnalysisApi.analyzeVisuals', () => {
  it('posts the file as multipart form data', async () => {
    api.post.mockResolvedValue({ data: { findings: [] } });
    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' });

    const result = await imageVisualAnalysisApi.analyzeVisuals(file);

    expect(api.post).toHaveBeenCalledWith(
      '/api/image/visual-analysis',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    const formData = api.post.mock.calls[0][1];
    expect(formData.get('file')).toBe(file);
    expect(result).toEqual({ findings: [] });
  });
});

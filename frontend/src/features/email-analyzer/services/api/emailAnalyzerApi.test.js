import api from '../../../../core/services/baseApi';
import { emailAnalyzerApi } from './emailAnalyzerApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('emailAnalyzerApi.analyzeEmail', () => {
  it('posts the file as multipart form data', async () => {
    api.post.mockResolvedValue({ data: { summary: 'ok' } });
    const file = new File(['content'], 'sample.eml', { type: 'message/rfc822' });

    const result = await emailAnalyzerApi.analyzeEmail(file);

    expect(api.post).toHaveBeenCalledWith(
      '/api/email/analyze',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    const [, formData] = api.post.mock.calls[0];
    expect(formData.get('file')).toBe(file);
    expect(result).toEqual({ summary: 'ok' });
  });
});

describe('emailAnalyzerApi.exportReport', () => {
  it('requests the report as a blob with the given format/locale', async () => {
    const blob = new Blob(['pdf']);
    api.post.mockResolvedValue({ data: blob });

    const result = await emailAnalyzerApi.exportReport({ id: 1 }, 'pdf', 'en');

    expect(api.post).toHaveBeenCalledWith('/api/email/report', { id: 1 }, {
      params: { format: 'pdf', locale: 'en' },
      responseType: 'blob',
    });
    expect(result).toBe(blob);
  });
});

import api from '../../../../core/services/baseApi';
import { aiAssistantApi } from './aiAssistantApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('aiAssistantApi.analyzeMailBody', () => {
  it('posts the input and unwraps analysis_result', async () => {
    api.post.mockResolvedValue({ data: { analysis_result: 'looks phishy' } });

    const result = await aiAssistantApi.analyzeMailBody('mail body text');

    expect(api.post).toHaveBeenCalledWith('/api/email/ai-analysis', { input: 'mail body text' });
    expect(result).toBe('looks phishy');
  });
});

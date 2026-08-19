import api from '../../../../core/services/baseApi';
import { dorkRunnerApi } from './dorkRunnerApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { get: vi.fn(), post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('dorkRunnerApi.getTemplates', () => {
  it('requests templates for the given target type', async () => {
    api.get.mockResolvedValue({ data: [{ key: 'site_search' }] });

    const result = await dorkRunnerApi.getTemplates('domain');

    expect(api.get).toHaveBeenCalledWith('/api/dork-runner/templates', {
      params: { target_type: 'domain' },
    });
    expect(result).toEqual([{ key: 'site_search' }]);
  });
});

describe('dorkRunnerApi.runDorks', () => {
  it('posts the run request with snake_case fields', async () => {
    api.post.mockResolvedValue({ data: { results: [] } });

    const result = await dorkRunnerApi.runDorks({
      target: 'example.com',
      targetType: 'domain',
      engine: 'duckduckgo',
      templateKeys: ['site_search', 'filetype_pdf'],
    });

    expect(api.post).toHaveBeenCalledWith('/api/dork-runner/run', {
      target: 'example.com',
      target_type: 'domain',
      engine: 'duckduckgo',
      template_keys: ['site_search', 'filetype_pdf'],
    });
    expect(result).toEqual({ results: [] });
  });
});

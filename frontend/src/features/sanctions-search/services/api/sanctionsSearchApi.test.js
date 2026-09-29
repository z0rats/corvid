import api from '../../../../core/services/baseApi';
import { sanctionsSearchApi } from './sanctionsSearchApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('sanctionsSearchApi.search', () => {
  it('requests a search with q/schema/limit params', async () => {
    api.get.mockResolvedValue({ data: { matches: [] } });

    const result = await sanctionsSearchApi.search({ query: 'Jane Doe', schema: 'Person', limit: 50 });

    expect(api.get).toHaveBeenCalledWith('/api/sanctions-search/search', {
      params: { q: 'Jane Doe', schema: 'Person', limit: 50 },
    });
    expect(result).toEqual({ matches: [] });
  });
});

describe('sanctionsSearchApi.getSchemas', () => {
  it('requests the list of available schemas', async () => {
    api.get.mockResolvedValue({ data: ['Person', 'Vessel'] });

    const result = await sanctionsSearchApi.getSchemas();

    expect(api.get).toHaveBeenCalledWith('/api/sanctions-search/schemas');
    expect(result).toEqual(['Person', 'Vessel']);
  });
});

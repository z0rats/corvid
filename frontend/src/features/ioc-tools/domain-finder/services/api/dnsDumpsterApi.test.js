import api from '../../../../../core/services/baseApi';
import { dnsDumpsterApi } from './dnsDumpsterApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('dnsDumpsterApi.lookupDnsDumpster', () => {
  it('requests DNSDumpster data for the given domain', async () => {
    api.get.mockResolvedValue({ data: { domains: [] } });

    const result = await dnsDumpsterApi.lookupDnsDumpster('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/dnsdumpster/example.com');
    expect(result).toEqual({ domains: [] });
  });
});

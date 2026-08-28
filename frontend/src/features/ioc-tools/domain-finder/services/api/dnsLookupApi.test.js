import api from '../../../../../core/services/baseApi';
import { dnsLookupApi } from './dnsLookupApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('dnsLookupApi.lookupDns', () => {
  it('requests DNS records for the given domain', async () => {
    api.get.mockResolvedValue({ data: { records: { A: ['1.2.3.4'] } } });

    const result = await dnsLookupApi.lookupDns('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/dns/example.com');
    expect(result).toEqual({ records: { A: ['1.2.3.4'] } });
  });
});

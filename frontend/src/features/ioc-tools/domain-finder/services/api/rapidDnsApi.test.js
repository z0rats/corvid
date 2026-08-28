import api from '../../../../../core/services/baseApi';
import { rapidDnsApi } from './rapidDnsApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('rapidDnsApi.lookupRapidDnsSubdomains', () => {
  it('requests RapidDNS subdomains for the given domain', async () => {
    api.get.mockResolvedValue({ data: { subdomains: ['mail.example.com'] } });

    const result = await rapidDnsApi.lookupRapidDnsSubdomains('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/rapiddns-subdomains/example.com');
    expect(result).toEqual({ subdomains: ['mail.example.com'] });
  });
});

import api from '../../../../../core/services/baseApi';
import { whoisLookupApi } from './whoisLookupApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('whoisLookupApi.lookupWhois', () => {
  it('requests WHOIS/RDAP data for the given domain', async () => {
    api.get.mockResolvedValue({ data: { registrar: 'Example Registrar' } });

    const result = await whoisLookupApi.lookupWhois('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/whois/example.com');
    expect(result).toEqual({ registrar: 'Example Registrar' });
  });
});

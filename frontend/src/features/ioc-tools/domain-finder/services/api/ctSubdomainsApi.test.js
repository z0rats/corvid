import api from '../../../../../core/services/baseApi';
import { ctSubdomainsApi } from './ctSubdomainsApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('ctSubdomainsApi.lookupCtSubdomains', () => {
  it('requests crt.sh subdomains for the given domain', async () => {
    api.get.mockResolvedValue({ data: { subdomains: ['a.example.com'] } });

    const result = await ctSubdomainsApi.lookupCtSubdomains('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/ct-subdomains/example.com');
    expect(result).toEqual({ subdomains: ['a.example.com'] });
  });
});

import api from '../../../../../core/services/baseApi';
import { hackertargetApi } from './hackertargetApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('hackertargetApi.lookupHackertargetSubdomains', () => {
  it('requests HackerTarget subdomains for the given domain', async () => {
    api.get.mockResolvedValue({ data: { subdomains: ['www.example.com'] } });

    const result = await hackertargetApi.lookupHackertargetSubdomains('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/hackertarget-subdomains/example.com');
    expect(result).toEqual({ subdomains: ['www.example.com'] });
  });
});

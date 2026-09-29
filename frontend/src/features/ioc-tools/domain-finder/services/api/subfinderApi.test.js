import api from '../../../../../core/services/baseApi';
import { subfinderApi } from './subfinderApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('subfinderApi.lookupSubfinderSubdomains', () => {
  it('requests subfinder subdomains for the given domain', async () => {
    api.get.mockResolvedValue({ data: { subdomains: ['www.example.com'] } });

    const result = await subfinderApi.lookupSubfinderSubdomains('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/subfinder-subdomains/example.com');
    expect(result).toEqual({ subdomains: ['www.example.com'] });
  });
});

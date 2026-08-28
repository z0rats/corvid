import api from '../../../../../core/services/baseApi';
import { webCheckApi } from './webCheckApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('webCheckApi.getSslInfo', () => {
  it('requests TLS certificate info for the given domain', async () => {
    api.get.mockResolvedValue({ data: { issuer: 'Let\'s Encrypt' } });

    const result = await webCheckApi.getSslInfo('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/ssl-info/example.com');
    expect(result).toEqual({ issuer: 'Let\'s Encrypt' });
  });
});

describe('webCheckApi.getSecurityHeaders', () => {
  it('requests security headers for the given domain', async () => {
    api.get.mockResolvedValue({ data: { headers: {} } });

    const result = await webCheckApi.getSecurityHeaders('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/security-headers/example.com');
    expect(result).toEqual({ headers: {} });
  });
});

describe('webCheckApi.getDnssec', () => {
  it('requests DNSSEC status for the given domain', async () => {
    api.get.mockResolvedValue({ data: { enabled: true } });

    const result = await webCheckApi.getDnssec('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/dnssec/example.com');
    expect(result).toEqual({ enabled: true });
  });
});

describe('webCheckApi.getBlocklist', () => {
  it('requests DNS-blocklist status for the given domain', async () => {
    api.get.mockResolvedValue({ data: { blocked: false } });

    const result = await webCheckApi.getBlocklist('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/blocklist/example.com');
    expect(result).toEqual({ blocked: false });
  });
});

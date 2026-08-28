import api from '../../../../../core/services/baseApi';
import { domainMonitoringApi } from './domainMonitoringApi';

vi.mock('../../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('domainMonitoringApi.searchDomains', () => {
  it('requests typosquat matches via GET for the given domain', async () => {
    api.get.mockResolvedValue({ data: { results: [] } });

    const result = await domainMonitoringApi.searchDomains('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/lookup/example.com');
    expect(result).toEqual({ results: [] });
  });
});

describe('domainMonitoringApi.searchDomainsPost', () => {
  it('posts the domain in the request body', async () => {
    api.post.mockResolvedValue({ data: { results: [] } });

    const result = await domainMonitoringApi.searchDomainsPost('example.com');

    expect(api.post).toHaveBeenCalledWith('/api/domain/lookup', { domain: 'example.com' });
    expect(result).toEqual({ results: [] });
  });
});

describe('domainMonitoringApi.checkHealth', () => {
  it('requests the health endpoint', async () => {
    api.get.mockResolvedValue({ data: { status: 'ok' } });

    const result = await domainMonitoringApi.checkHealth();

    expect(api.get).toHaveBeenCalledWith('/api/domain/health');
    expect(result).toEqual({ status: 'ok' });
  });
});

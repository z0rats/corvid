import api from '../../../../../core/services/baseApi';
import { waybackApi } from './waybackApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('waybackApi.lookupWayback', () => {
  it('requests wayback snapshots for the domain without a path filter', async () => {
    api.get.mockResolvedValue({ data: { snapshots: [] } });

    const result = await waybackApi.lookupWayback('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/wayback/example.com', {
      params: undefined,
    });
    expect(result).toEqual({ snapshots: [] });
  });

  it('passes a path filter as a query param when given', async () => {
    api.get.mockResolvedValue({ data: { snapshots: [] } });

    await waybackApi.lookupWayback('example.com', '/login');

    expect(api.get).toHaveBeenCalledWith('/api/domain/wayback/example.com', {
      params: { path: '/login' },
    });
  });
});

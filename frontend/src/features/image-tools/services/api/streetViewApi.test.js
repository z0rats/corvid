import api from '../../../../core/services/baseApi';
import { streetViewApi } from './streetViewApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('streetViewApi.getKey', () => {
  it('requests the configured Google Maps key', async () => {
    api.get.mockResolvedValue({ data: { key: 'abc123' } });

    const result = await streetViewApi.getKey();

    expect(api.get).toHaveBeenCalledWith('/api/image/street-view-key');
    expect(result).toEqual({ key: 'abc123' });
  });
});

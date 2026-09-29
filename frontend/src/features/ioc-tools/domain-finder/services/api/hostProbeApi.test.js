import api from '../../../../../core/services/baseApi';
import { hostProbeApi } from './hostProbeApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('hostProbeApi.probeHost', () => {
  it('requests a host probe for the given domain', async () => {
    api.get.mockResolvedValue({ data: { reachable: true } });

    const result = await hostProbeApi.probeHost('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/host-probe/example.com');
    expect(result).toEqual({ reachable: true });
  });
});

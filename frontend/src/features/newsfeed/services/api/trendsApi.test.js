import api from '../../../../core/services/baseApi';
import { trendsApi } from './trendsApi';

vi.mock('../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('trendsApi.getTitleWordFrequency', () => {
  it('requests top title words for the given limit/time range', async () => {
    api.get.mockResolvedValue({ data: { words: [] } });

    const result = await trendsApi.getTitleWordFrequency(10, '7d');

    expect(api.get).toHaveBeenCalledWith('/api/newsfeed/words/top?limit=10&time_range=7d');
    expect(result).toEqual({ words: [] });
  });
});

describe('trendsApi.getTopIocs', () => {
  it('requests top IOCs for the given type/limit/time range', async () => {
    api.get.mockResolvedValue({ data: { iocs: [] } });

    const result = await trendsApi.getTopIocs('ip', 10, '30d');

    expect(api.get).toHaveBeenCalledWith('/api/newsfeed/iocs/top?ioc_type=ip&limit=10&time_range=30d');
    expect(result).toEqual({ iocs: [] });
  });
});

describe('trendsApi.getTopCves', () => {
  it('requests top CVEs for the given limit/time range', async () => {
    api.get.mockResolvedValue({ data: { cves: [] } });

    const result = await trendsApi.getTopCves(5, '24h');

    expect(api.get).toHaveBeenCalledWith('/api/newsfeed/cves/top?limit=5&time_range=24h');
    expect(result).toEqual({ cves: [] });
  });
});

describe('trendsApi.getIocTypeDistribution', () => {
  it('requests the IOC type distribution for the given time range', async () => {
    api.get.mockResolvedValue({ data: { distribution: {} } });

    const result = await trendsApi.getIocTypeDistribution('7d');

    expect(api.get).toHaveBeenCalledWith('/api/newsfeed/iocs/distribution?time_range=7d');
    expect(result).toEqual({ distribution: {} });
  });
});

import api from '../../../../../core/services/baseApi';
import { temporalAnalysisApi } from './temporalAnalysisApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { get: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('temporalAnalysisApi.lookupTemporalAnalysis', () => {
  it('requests the temporal analysis timeline for the domain', async () => {
    api.get.mockResolvedValue({ data: { events: [] } });

    const result = await temporalAnalysisApi.lookupTemporalAnalysis('example.com');

    expect(api.get).toHaveBeenCalledWith('/api/domain/temporal-analysis/example.com');
    expect(result).toEqual({ events: [] });
  });
});

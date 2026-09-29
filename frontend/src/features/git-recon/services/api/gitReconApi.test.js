import api from '../../../../core/services/baseApi';
import { gitReconApi } from './gitReconApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
  baseURL: 'http://backend.test',
}));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('gitReconApi.listHistory', () => {
  it('requests paginated history with default skip/limit', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await gitReconApi.listHistory();

    expect(api.get).toHaveBeenCalledWith('/api/git-recon/history', { params: { skip: 0, limit: 100 } });
    expect(result).toEqual({ items: [] });
  });
});

describe('gitReconApi.getHistory', () => {
  it('requests a single history entry by id', async () => {
    api.get.mockResolvedValue({ data: { id: 'search-1' } });

    const result = await gitReconApi.getHistory('search-1');

    expect(api.get).toHaveBeenCalledWith('/api/git-recon/history/search-1');
    expect(result).toEqual({ id: 'search-1' });
  });
});

describe('gitReconApi.deleteHistory', () => {
  it('deletes a history entry by id', async () => {
    api.delete.mockResolvedValue({});

    await gitReconApi.deleteHistory('search-1');

    expect(api.delete).toHaveBeenCalledWith('/api/git-recon/history/search-1');
  });
});

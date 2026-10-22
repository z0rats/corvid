import api from '../baseApi';
import { investigationsService } from './investigationsService';

vi.mock('../baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('investigationsService', () => {
  it('creates an investigation', async () => {
    api.post.mockResolvedValue({ data: { id: 1 } });
    await expect(investigationsService.create('Case')).resolves.toEqual({ id: 1 });
    expect(api.post).toHaveBeenCalledWith('/api/investigations', { name: 'Case', notes: null });
  });

  it('adds a run as feature + run_id', async () => {
    api.post.mockResolvedValue({ data: { id: 7 } });
    await investigationsService.addItem(1, 'ioc_lookup', 42, 'n');
    expect(api.post).toHaveBeenCalledWith('/api/investigations/1/items', {
      feature: 'ioc_lookup',
      run_id: 42,
      note: 'n',
    });
  });

  it('patches an item note and the investigation', async () => {
    api.patch.mockResolvedValue({ data: {} });
    await investigationsService.updateItem(1, 7, 'x');
    await investigationsService.update(1, { notes: null });
    expect(api.patch).toHaveBeenCalledWith('/api/investigations/1/items/7', { note: 'x' });
    expect(api.patch).toHaveBeenCalledWith('/api/investigations/1', { notes: null });
  });

  it('removes investigations and items', async () => {
    await investigationsService.remove(1);
    await investigationsService.removeItem(1, 7);
    expect(api.delete).toHaveBeenCalledWith('/api/investigations/1');
    expect(api.delete).toHaveBeenCalledWith('/api/investigations/1/items/7');
  });

  it('describes the report download for the authenticated client', () => {
    expect(investigationsService.reportRequest(1, 'pdf', 'en')).toEqual({
      path: '/api/investigations/1/report',
      params: { format: 'pdf', locale: 'en' },
      fallbackName: 'investigation-1.pdf',
    });
  });

  it('sends the graph type filter as repeated params, or none', async () => {
    api.get.mockResolvedValue({ data: {} });
    await investigationsService.graph(1, ['ip', 'asn']);
    await investigationsService.graph(1);
    expect(api.get).toHaveBeenNthCalledWith(1, '/api/investigations/1/graph', {
      params: { types: ['ip', 'asn'] },
      paramsSerializer: { indexes: null },
    });
    expect(api.get).toHaveBeenNthCalledWith(2, '/api/investigations/1/graph', {
      params: undefined,
      paramsSerializer: { indexes: null },
    });
  });

  it('lists memberships, features and investigations', async () => {
    api.get.mockResolvedValue({ data: [] });
    await investigationsService.memberships('reddit_search', 3);
    await investigationsService.features();
    await investigationsService.list();
    await investigationsService.get(2);
    expect(api.get).toHaveBeenCalledWith('/api/investigations/memberships', {
      params: { feature: 'reddit_search', run_id: 3 },
    });
    expect(api.get).toHaveBeenCalledWith('/api/investigations/features');
    expect(api.get).toHaveBeenCalledWith('/api/investigations');
    expect(api.get).toHaveBeenCalledWith('/api/investigations/2');
  });
});

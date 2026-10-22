import api from '../../../../core/services/baseApi';
import { telegramSearchApi } from './telegramSearchApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), delete: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('telegramSearchApi', () => {
  it('lists history with skip/limit', async () => {
    api.get.mockResolvedValue({ data: [{ id: 1 }] });

    expect(await telegramSearchApi.listSearches(5, 10)).toEqual([{ id: 1 }]);
    expect(api.get).toHaveBeenCalledWith('/api/telegram-search/history', { params: { skip: 5, limit: 10 } });
  });

  it('gets one run', async () => {
    api.get.mockResolvedValue({ data: { id: 3 } });

    expect(await telegramSearchApi.getSearch(3)).toEqual({ id: 3 });
    expect(api.get).toHaveBeenCalledWith('/api/telegram-search/history/3');
  });

  it('deletes one run', async () => {
    await telegramSearchApi.deleteSearch(3);
    expect(api.delete).toHaveBeenCalledWith('/api/telegram-search/history/3');
  });
});

import { renderHook, waitFor } from '@testing-library/react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { useFeedReliability } from './useFeedReliability';

vi.mock('../../services/api/settingsApi', () => ({
  newsfeedSettingsApi: { getNewsfeeds: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('useFeedReliability', () => {
  it('maps feed names to grades, skipping unrated feeds', async () => {
    vi.mocked(newsfeedSettingsApi.getNewsfeeds).mockResolvedValue([
      { name: 'Krebs', reliability: 'B' },
      { name: 'Unrated' },
    ]);

    const { result } = renderHook(() => useFeedReliability());

    await waitFor(() => expect(result.current).toEqual({ Krebs: 'B' }));
  });

  it('stays empty when the feed list cannot be loaded', async () => {
    vi.mocked(newsfeedSettingsApi.getNewsfeeds).mockRejectedValue(new Error('404'));

    const { result } = renderHook(() => useFeedReliability());

    await waitFor(() => expect(newsfeedSettingsApi.getNewsfeeds).toHaveBeenCalled());
    expect(result.current).toEqual({});
  });
});

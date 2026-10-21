import { renderHook, act } from '@testing-library/react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { useIconManagement } from './useIconManagement';

vi.mock('../../services/api/settingsApi', () => ({
  newsfeedSettingsApi: {
    deleteFeedIcon: vi.fn(),
    refetchFeedIcon: vi.fn(),
    refetchAllMissingIcons: vi.fn(),
    getNewsfeeds: vi.fn(),
  },
}));

const FEEDS = { 'Хабр Блог': { name: 'Хабр Блог', icon: 'abc.png', icon_id: 'abc.png' } };

function setup(feeds = FEEDS) {
  const setFeeds = vi.fn();
  const { result, unmount } = renderHook(() => useIconManagement(feeds, setFeeds));
  return { result, setFeeds, unmount };
}

const b64utf8 = (s) => Buffer.from(s, 'utf-8').toString('base64');

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe('useIconManagement', () => {
  it('deleteIcon base64-encodes non-ASCII feed names as UTF-8', async () => {
    newsfeedSettingsApi.deleteFeedIcon.mockResolvedValue({ message: 'ok' });
    const { result } = setup();
    await act(async () => result.current.deleteIcon('Хабр Блог'));
    expect(newsfeedSettingsApi.deleteFeedIcon).toHaveBeenCalledWith(b64utf8('Хабр Блог'));
  });

  it('deleteIcon resets locally, then reloads the feeds from the server once', async () => {
    newsfeedSettingsApi.deleteFeedIcon.mockResolvedValue({ message: 'Icon deleted' });
    newsfeedSettingsApi.getNewsfeeds.mockResolvedValue([{ name: 'Хабр Блог', icon: 'fresh.png' }]);
    const { result, setFeeds } = setup();

    let out;
    await act(async () => { out = await result.current.deleteIcon('Хабр Блог'); });
    expect(out).toEqual({ success: true, message: 'Icon deleted' });
    expect(setFeeds).toHaveBeenCalledWith({
      'Хабр Блог': { name: 'Хабр Блог', icon: 'default.png', icon_id: null },
    });
    expect(newsfeedSettingsApi.getNewsfeeds).not.toHaveBeenCalled();

    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
    expect(newsfeedSettingsApi.getNewsfeeds).toHaveBeenCalledTimes(1);
    expect(setFeeds).toHaveBeenLastCalledWith({ 'Хабр Блог': { name: 'Хабр Блог', icon: 'fresh.png' } });
  });

  it('the pending reload is cancelled on unmount', async () => {
    newsfeedSettingsApi.deleteFeedIcon.mockResolvedValue({});
    const { result, unmount } = setup();
    await act(async () => result.current.deleteIcon('Хабр Блог'));
    unmount();
    await vi.advanceTimersByTimeAsync(2000);
    expect(newsfeedSettingsApi.getNewsfeeds).not.toHaveBeenCalled();
  });

  it('deleteIcon reports a failure without touching state', async () => {
    newsfeedSettingsApi.deleteFeedIcon.mockRejectedValue(new Error('404'));
    const { result, setFeeds } = setup();
    let out;
    await act(async () => { out = await result.current.deleteIcon('Хабр Блог'); });
    expect(out.success).toBe(false);
    expect(setFeeds).not.toHaveBeenCalled();
  });

  it('refetchIcon applies the new icon only on success', async () => {
    newsfeedSettingsApi.refetchFeedIcon
      .mockResolvedValueOnce({ success: true, icon_id: 'new.png', message: 'ok' })
      .mockResolvedValueOnce({ success: false, message: 'Could not download favicon' });
    const { result, setFeeds } = setup();

    let out;
    await act(async () => { out = await result.current.refetchIcon('Хабр Блог'); });
    expect(out).toEqual({ success: true, message: 'ok', iconId: 'new.png' });
    const updater = setFeeds.mock.calls[0][0];
    expect(updater(FEEDS)['Хабр Блог']).toEqual({ name: 'Хабр Блог', icon: 'new.png', icon_id: 'new.png' });

    await act(async () => { out = await result.current.refetchIcon('Хабр Блог'); });
    expect(out.success).toBe(false);
    expect(setFeeds).toHaveBeenCalledTimes(1);
  });

  it('refetchAllMissingIcons reloads the feed map and reports totals', async () => {
    newsfeedSettingsApi.refetchAllMissingIcons.mockResolvedValue({ total: 3, succeeded: 2, failed: 1, results: [] });
    newsfeedSettingsApi.getNewsfeeds.mockResolvedValue([{ name: 'a' }, { name: 'b' }]);
    const { result, setFeeds } = setup();
    let out;
    await act(async () => { out = await result.current.refetchAllMissingIcons(); });
    expect(out).toEqual({ success: true, total: 3, succeeded: 2, failed: 1, results: [] });
    expect(setFeeds).toHaveBeenCalledWith({ a: { name: 'a' }, b: { name: 'b' } });
  });

  it('refetchAllMissingIcons failure', async () => {
    newsfeedSettingsApi.refetchAllMissingIcons.mockRejectedValue(new Error('x'));
    const { result } = setup();
    let out;
    await act(async () => { out = await result.current.refetchAllMissingIcons(); });
    expect(out.success).toBe(false);
  });
});

import { renderHook, act, waitFor } from '@testing-library/react';
import { newsfeedApi } from '../../services/api/newsfeedApi';
import { useHeadlines } from './useHeadlinesApi';

vi.mock('../../services/api/newsfeedApi', () => ({ newsfeedApi: { getRecentArticles: vi.fn() } }));

const HEADLINES = [
  { id: 1, feedname: 'BleepingComputer', title: 'Ransomware hits hospital', date: '2026-10-01T10:00:00Z' },
  { id: 2, feedname: 'The Hacker News', title: 'New zero-day in VPN', date: '2026-10-03T10:00:00Z' },
  { id: 3, feedname: 'bleepingcomputer', title: 'Patch Tuesday', date: '2026-10-02T10:00:00Z' },
];

async function setup() {
  newsfeedApi.getRecentArticles.mockResolvedValue(HEADLINES);
  const hook = renderHook(() => useHeadlines());
  await waitFor(() => expect(hook.result.current.headlines).toHaveLength(3));
  return hook.result;
}

const ids = (result) => result.current.displayData.map((h) => h.id);

afterEach(() => vi.clearAllMocks());

describe('useHeadlines', () => {
  it('defaults to the last 2 days, newest first', async () => {
    const result = await setup();
    expect(newsfeedApi.getRecentArticles).toHaveBeenCalledWith('2d');
    expect(ids(result)).toEqual([2, 3, 1]);
  });

  it('sorting the same column twice flips direction', async () => {
    const result = await setup();
    act(() => result.current.handleSort('date'));
    expect(result.current.order).toBe('asc');
    expect(ids(result)).toEqual([1, 3, 2]);
    act(() => result.current.handleSort('date'));
    expect(result.current.order).toBe('desc');

    act(() => result.current.handleSort('title'));
    expect(result.current.order).toBe('asc');
    expect(result.current.displayData.map((h) => h.title)).toEqual([
      'New zero-day in VPN', 'Patch Tuesday', 'Ransomware hits hospital',
    ]);
  });

  it('source and title filters are case-insensitive and combine', async () => {
    const result = await setup();
    act(() => result.current.setSourceFilter('BLEEPING'));
    expect(result.current.filteredCount).toBe(2);
    act(() => result.current.setTitleFilter('patch'));
    expect(ids(result)).toEqual([3]);
  });

  it('paginates and resets to the first page when rows-per-page changes', async () => {
    const result = await setup();
    act(() => result.current.handleChangeRowsPerPage({ target: { value: '2' } }));
    expect(ids(result)).toEqual([2, 3]);
    act(() => result.current.handleChangePage(null, 1));
    expect(ids(result)).toEqual([1]);
    act(() => result.current.handleChangeRowsPerPage({ target: { value: '10' } }));
    expect(result.current.page).toBe(0);
  });

  it('changing the time window or refreshing refetches', async () => {
    const result = await setup();
    act(() => result.current.setTimeFilter('7d'));
    await waitFor(() => expect(newsfeedApi.getRecentArticles).toHaveBeenLastCalledWith('7d'));
    act(() => result.current.handleRefresh());
    await waitFor(() => expect(newsfeedApi.getRecentArticles).toHaveBeenCalledTimes(3));
  });

  it('a failed fetch keeps the list empty without throwing', async () => {
    newsfeedApi.getRecentArticles.mockRejectedValue(new Error('down'));
    const { result } = renderHook(() => useHeadlines());
    await waitFor(() => expect(newsfeedApi.getRecentArticles).toHaveBeenCalled());
    expect(result.current.displayData).toEqual([]);
  });
});

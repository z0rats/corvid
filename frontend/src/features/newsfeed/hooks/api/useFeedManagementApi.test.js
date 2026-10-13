import { renderHook, act, waitFor } from '@testing-library/react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { useFeedManagement } from './useFeedManagementApi';

vi.mock('../../services/api/settingsApi', () => ({
  newsfeedSettingsApi: {
    getNewsfeeds: vi.fn(), setNewsfeedReliability: vi.fn(), enableNewsfeed: vi.fn(), disableNewsfeed: vi.fn(),
  },
}));

const feedsFixture = () => [
  { name: 'A', url: 'https://a.test/rss', enabled: true, reliability: 'C' },
  { name: 'B', url: 'https://b.test/rss', enabled: true },
];

const setup = async () => {
  newsfeedSettingsApi.getNewsfeeds.mockResolvedValue(feedsFixture());
  const hook = renderHook(() => useFeedManagement());
  await waitFor(() => expect(hook.result.current.loading).toBe(false));
  return hook;
};

afterEach(() => vi.clearAllMocks());

describe('useFeedManagement.setReliability', () => {
  it('applies the grade optimistically and keeps it on success', async () => {
    newsfeedSettingsApi.setNewsfeedReliability.mockResolvedValue({});
    const { result } = await setup();

    let outcome;
    await act(async () => {
      outcome = await result.current.setReliability('B', 'A');
    });

    expect(outcome).toEqual({ success: true, reliability: 'A' });
    expect(newsfeedSettingsApi.setNewsfeedReliability).toHaveBeenCalledWith('B', 'A');
    expect(result.current.feeds.B.reliability).toBe('A');
  });

  it('rolls back only the failed feed, not edits made to other feeds meanwhile', async () => {
    let rejectFirst;
    newsfeedSettingsApi.setNewsfeedReliability
      .mockImplementationOnce(() => new Promise((_, reject) => { rejectFirst = reject; }))
      .mockResolvedValueOnce({});
    const { result } = await setup();

    let slow;
    act(() => {
      slow = result.current.setReliability('A', 'D');
    });
    await act(async () => {
      await result.current.setReliability('B', 'A');
    });
    await act(async () => {
      rejectFirst(new Error('boom'));
      await slow;
    });

    expect(result.current.feeds.A.reliability).toBe('C');
    expect(result.current.feeds.B.reliability).toBe('A');
  });

  it('reports failure for an unknown feed without calling the API', async () => {
    const { result } = await setup();

    let outcome;
    await act(async () => {
      outcome = await result.current.setReliability('missing', 'A');
    });

    expect(outcome).toEqual({ success: false });
    expect(newsfeedSettingsApi.setNewsfeedReliability).not.toHaveBeenCalled();
  });
});

describe('useFeedManagement.toggleFeed', () => {
  it('rolls back only the enabled flag, keeping a grade set while the toggle was in flight', async () => {
    let rejectToggle;
    newsfeedSettingsApi.disableNewsfeed.mockImplementationOnce(
      () => new Promise((_, reject) => { rejectToggle = reject; }),
    );
    newsfeedSettingsApi.setNewsfeedReliability.mockResolvedValue({});
    const { result } = await setup();

    let toggle;
    act(() => {
      toggle = result.current.toggleFeed('A');
    });
    expect(result.current.feeds.A.enabled).toBe(false);
    await act(async () => {
      await result.current.setReliability('A', 'B');
    });
    await act(async () => {
      rejectToggle(new Error('boom'));
      await toggle;
    });

    expect(result.current.feeds.A.enabled).toBe(true);
    expect(result.current.feeds.A.reliability).toBe('B');
  });
});

import { renderHook, waitFor } from '@testing-library/react';
import { useNewsfeedMentions } from './useNewsfeedMentions';
import { iocLookupApi } from '../../../../shared/services/api/iocLookupApi';

vi.mock('../../../../shared/services/api/iocLookupApi');

afterEach(() => vi.clearAllMocks());

describe('useNewsfeedMentions', () => {
  it('returns an empty array and does not call the API when no IOC is given', () => {
    const { result } = renderHook(() => useNewsfeedMentions(''));
    expect(result.current).toEqual([]);
    expect(iocLookupApi.fetchNewsfeedMentions).not.toHaveBeenCalled();
  });

  it('fetches and returns mentions for the given IOC', async () => {
    iocLookupApi.fetchNewsfeedMentions.mockResolvedValue({ mentions: [{ title: 'Article' }] });
    const { result } = renderHook(() => useNewsfeedMentions('1.2.3.4'));

    await waitFor(() => expect(result.current).toEqual([{ title: 'Article' }]));

    expect(iocLookupApi.fetchNewsfeedMentions).toHaveBeenCalledWith(
      '1.2.3.4',
      expect.objectContaining({ signal: expect.anything() }),
    );
  });

  it('defaults to an empty array when the response has no mentions field', async () => {
    iocLookupApi.fetchNewsfeedMentions.mockResolvedValue({});
    const { result } = renderHook(() => useNewsfeedMentions('1.2.3.4'));

    await waitFor(() => expect(iocLookupApi.fetchNewsfeedMentions).toHaveBeenCalled());

    expect(result.current).toEqual([]);
  });

  it('clears mentions on a non-abort failure rather than leaving stale data', async () => {
    iocLookupApi.fetchNewsfeedMentions.mockRejectedValue(new Error('server error'));
    const { result } = renderHook(() => useNewsfeedMentions('1.2.3.4'));

    await waitFor(() => expect(result.current).toEqual([]));
  });

  it('re-fetches when the ioc prop changes', async () => {
    iocLookupApi.fetchNewsfeedMentions
      .mockResolvedValueOnce({ mentions: [{ title: 'First' }] })
      .mockResolvedValueOnce({ mentions: [{ title: 'Second' }] });
    const { result, rerender } = renderHook(({ ioc }) => useNewsfeedMentions(ioc), {
      initialProps: { ioc: 'a.com' },
    });
    await waitFor(() => expect(result.current).toEqual([{ title: 'First' }]));

    rerender({ ioc: 'b.com' });

    await waitFor(() => expect(result.current).toEqual([{ title: 'Second' }]));
  });
});

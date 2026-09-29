import { act, renderHook } from '@testing-library/react';
import { useInstagramSearch } from './useInstagramSearch';
import { instagramSearchApi } from '../../services/api/instagramSearchApi';

vi.mock('../../services/api/instagramSearchApi');
vi.mock('../../../../core/hooks/usePrefillFromQuery', () => ({
  usePrefillFromQuery: vi.fn(),
}));

afterEach(() => vi.clearAllMocks());

describe('useInstagramSearch — lookupProfile', () => {
  it('does nothing for a blank username', async () => {
    const { result } = renderHook(() => useInstagramSearch());

    await act(async () => result.current.lookupProfile('   '));

    expect(instagramSearchApi.lookupProfile).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });

  it('trims and looks up the current username state, populating the result', async () => {
    instagramSearchApi.lookupProfile.mockResolvedValue({ username: 'someuser', mode: 'anonymous' });
    const { result } = renderHook(() => useInstagramSearch());

    act(() => result.current.setUsername('  someuser  '));
    await act(async () => result.current.lookupProfile());

    expect(instagramSearchApi.lookupProfile).toHaveBeenCalledWith('someuser');
    expect(result.current.result).toEqual({ username: 'someuser', mode: 'anonymous' });
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('looks up an explicit override instead of the username state', async () => {
    instagramSearchApi.lookupProfile.mockResolvedValue({ username: 'override', mode: 'anonymous' });
    const { result } = renderHook(() => useInstagramSearch());

    await act(async () => result.current.lookupProfile('override'));

    expect(instagramSearchApi.lookupProfile).toHaveBeenCalledWith('override');
  });

  it('surfaces the response detail message on failure and clears loading', async () => {
    instagramSearchApi.lookupProfile.mockRejectedValue({
      response: { data: { detail: "Instagram profile 'ghost' does not exist" } },
    });
    const { result } = renderHook(() => useInstagramSearch());

    await act(async () => result.current.lookupProfile('ghost'));

    expect(result.current.error).toBe("Instagram profile 'ghost' does not exist");
    expect(result.current.loading).toBe(false);
    expect(result.current.result).toBeNull();
  });

  it('falls back to the generic error message when the response has no detail', async () => {
    instagramSearchApi.lookupProfile.mockRejectedValue(new Error('Network Error'));
    const { result } = renderHook(() => useInstagramSearch());

    await act(async () => result.current.lookupProfile('someuser'));

    expect(result.current.error).toBe('Network Error');
  });
});

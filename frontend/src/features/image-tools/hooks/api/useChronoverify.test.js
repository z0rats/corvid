import { act, renderHook, waitFor } from '@testing-library/react';
import { useChronoverify } from './useChronoverify';
import { chronoverifyApi } from '../../services/api/chronoverifyApi';

vi.mock('../../services/api/chronoverifyApi');

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('useChronoverify', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no result and no error', () => {
    const { result } = renderHook(() => useChronoverify());

    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('populates the result on a successful check', async () => {
    const mockResult = { verdict: 'consistent', confidence: 0.72, summary: 'ok', signals: [] };
    chronoverifyApi.checkProvenance.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useChronoverify());

    await act(async () => {
      await result.current.checkProvenance(makeFile());
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.result).toEqual(mockResult);
    expect(result.current.error).toBeNull();
    expect(chronoverifyApi.checkProvenance).toHaveBeenCalledTimes(1);
  });

  it('surfaces the API error message on failure', async () => {
    chronoverifyApi.checkProvenance.mockRejectedValue({
      response: { data: { detail: 'ChronoVerify rate limit reached' } },
    });

    const { result } = renderHook(() => useChronoverify());

    await act(async () => {
      await result.current.checkProvenance(makeFile());
    });

    expect(result.current.error).toBe('ChronoVerify rate limit reached');
    expect(result.current.result).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('reset clears result and error', async () => {
    chronoverifyApi.checkProvenance.mockResolvedValue({ verdict: 'consistent' });

    const { result } = renderHook(() => useChronoverify());

    await act(async () => {
      await result.current.checkProvenance(makeFile());
    });
    expect(result.current.result).not.toBeNull();

    act(() => {
      result.current.reset();
    });

    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
  });
});

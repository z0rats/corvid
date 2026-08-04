import { act, renderHook, waitFor } from '@testing-library/react';
import { useImageCompare } from './useImageCompare';
import { imageCompareApi } from '../../services/api/imageCompareApi';

vi.mock('../../services/api/imageCompareApi');

function makeFile(name) {
  return new File(['fake image content'], name, { type: 'image/jpeg' });
}

describe('useImageCompare', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no result and no error', () => {
    const { result } = renderHook(() => useImageCompare());

    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('populates the result on a successful comparison', async () => {
    const mockResult = {
      left: { filename: 'a.jpg' },
      right: { filename: 'b.jpg' },
      field_diffs: [],
      summary: { match_count: 0, differ_count: 0, only_left_count: 0, only_right_count: 0 },
      phash_distance: 0,
      pixels_likely_match: true,
    };
    imageCompareApi.compareImages.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useImageCompare());

    await act(async () => {
      await result.current.compareImages(makeFile('a.jpg'), makeFile('b.jpg'));
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.result).toEqual(mockResult);
    expect(imageCompareApi.compareImages).toHaveBeenCalledTimes(1);
  });

  it('surfaces the API error message on failure', async () => {
    imageCompareApi.compareImages.mockRejectedValue({
      response: { data: { detail: 'Image comparison failed' } },
    });

    const { result } = renderHook(() => useImageCompare());

    await act(async () => {
      await result.current.compareImages(makeFile('a.jpg'), makeFile('b.jpg'));
    });

    expect(result.current.error).toBe('Image comparison failed');
    expect(result.current.result).toBeNull();
  });
});

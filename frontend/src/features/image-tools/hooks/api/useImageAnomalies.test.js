import { act, renderHook, waitFor } from '@testing-library/react';
import { useImageAnomalies } from './useImageAnomalies';
import { imageAnomalyApi } from '../../services/api/imageAnomalyApi';

vi.mock('../../services/api/imageAnomalyApi');

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('useImageAnomalies', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no result and no error', () => {
    const { result } = renderHook(() => useImageAnomalies());

    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('populates the result on a successful analysis', async () => {
    const mockResult = { filename: 'photo.jpg', findings: [], checks_run: 3 };
    imageAnomalyApi.analyzeAnomalies.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useImageAnomalies());

    await act(async () => {
      await result.current.analyzeAnomalies(makeFile());
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.result).toEqual(mockResult);
    expect(result.current.error).toBeNull();
    expect(imageAnomalyApi.analyzeAnomalies).toHaveBeenCalledTimes(1);
  });

  it('surfaces the API error message on failure', async () => {
    imageAnomalyApi.analyzeAnomalies.mockRejectedValue({
      response: { data: { detail: 'File is not a recognized image format' } },
    });

    const { result } = renderHook(() => useImageAnomalies());

    await act(async () => {
      await result.current.analyzeAnomalies(makeFile());
    });

    expect(result.current.error).toBe('File is not a recognized image format');
    expect(result.current.result).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});

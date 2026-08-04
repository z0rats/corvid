import { act, renderHook, waitFor } from '@testing-library/react';
import { useImageVisualAnalysis } from './useImageVisualAnalysis';
import { imageVisualAnalysisApi } from '../../services/api/imageVisualAnalysisApi';

vi.mock('../../services/api/imageVisualAnalysisApi');

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('useImageVisualAnalysis', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no result and no error', () => {
    const { result } = renderHook(() => useImageVisualAnalysis());

    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('populates the result on a successful analysis', async () => {
    const mockResult = {
      histograms: { red: [], green: [], blue: [], luminance: [], cb: [], cr: [] },
      vectorscope: { bin_count: 64, counts: [], max_count: 0 },
    };
    imageVisualAnalysisApi.analyzeVisuals.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useImageVisualAnalysis());

    await act(async () => {
      await result.current.analyzeVisuals(makeFile());
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.result).toEqual(mockResult);
    expect(imageVisualAnalysisApi.analyzeVisuals).toHaveBeenCalledTimes(1);
  });

  it('surfaces the API error message on failure', async () => {
    imageVisualAnalysisApi.analyzeVisuals.mockRejectedValue({
      response: { data: { detail: 'File is not a recognized image format' } },
    });

    const { result } = renderHook(() => useImageVisualAnalysis());

    await act(async () => {
      await result.current.analyzeVisuals(makeFile());
    });

    expect(result.current.error).toBe('File is not a recognized image format');
    expect(result.current.result).toBeNull();
  });
});

import { act, renderHook, waitFor } from '@testing-library/react';
import { useImageStructure } from './useImageStructure';
import { imageStructureApi } from '../../services/api/imageStructureApi';

vi.mock('../../services/api/imageStructureApi');

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('useImageStructure', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no result and no error', () => {
    const { result } = renderHook(() => useImageStructure());

    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('populates the result on a successful analysis', async () => {
    const mockResult = {
      markers: [{ marker_type: 'SOI', offset: 0 }],
      quantization_tables: [],
      huffman_tables: [],
      frame: { width: 100, height: 80, is_progressive: false, chroma_subsampling: '4:2:0' },
      overall_quality_estimate: 80,
    };
    imageStructureApi.analyzeStructure.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useImageStructure());

    await act(async () => {
      await result.current.analyzeStructure(makeFile());
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.result).toEqual(mockResult);
    expect(result.current.error).toBeNull();
    expect(imageStructureApi.analyzeStructure).toHaveBeenCalledTimes(1);
  });

  it('surfaces the API error message on failure', async () => {
    imageStructureApi.analyzeStructure.mockRejectedValue({
      response: { data: { detail: 'Not a valid JPEG file' } },
    });

    const { result } = renderHook(() => useImageStructure());

    await act(async () => {
      await result.current.analyzeStructure(makeFile());
    });

    expect(result.current.error).toBe('Not a valid JPEG file');
    expect(result.current.result).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});

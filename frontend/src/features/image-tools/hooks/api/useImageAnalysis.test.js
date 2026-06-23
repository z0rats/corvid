import { act, renderHook, waitFor } from '@testing-library/react';
import { useImageAnalysis } from './useImageAnalysis';
import { imageAnalyzerApi } from '../../services/api/imageAnalyzerApi';

jest.mock('../../services/api/imageAnalyzerApi');

// jsdom does not implement createObjectURL/revokeObjectURL.
beforeEach(() => {
  global.URL.createObjectURL = jest.fn(() => 'blob:mock-preview-url');
  global.URL.revokeObjectURL = jest.fn();
});

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('useImageAnalysis', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('starts with no result and no error', () => {
    const { result } = renderHook(() => useImageAnalysis());

    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('sets an error and does not call the API when no file is provided', async () => {
    const { result } = renderHook(() => useImageAnalysis());

    await act(async () => {
      await result.current.analyzeImage(null);
    });

    expect(result.current.error).toBe('No file provided');
    expect(imageAnalyzerApi.analyzeImage).not.toHaveBeenCalled();
  });

  it('populates result and preview URL on a successful analysis', async () => {
    const mockResult = { file_info: { filename: 'photo.jpg' }, hashes: {}, exif: {} };
    imageAnalyzerApi.analyzeImage.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useImageAnalysis());

    await act(async () => {
      await result.current.analyzeImage(makeFile());
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.result).toEqual(mockResult);
    expect(result.current.previewUrl).toBe('blob:mock-preview-url');
    expect(result.current.error).toBeNull();
    expect(imageAnalyzerApi.analyzeImage).toHaveBeenCalledTimes(1);
  });

  it('surfaces the API error message on failure', async () => {
    imageAnalyzerApi.analyzeImage.mockRejectedValue({
      response: { data: { detail: 'Image analysis failed' } },
    });

    const { result } = renderHook(() => useImageAnalysis());

    await act(async () => {
      await result.current.analyzeImage(makeFile());
    });

    expect(result.current.error).toBe('Image analysis failed');
    expect(result.current.result).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('resets state', async () => {
    imageAnalyzerApi.analyzeImage.mockResolvedValue({ file_info: {}, hashes: {}, exif: {} });
    const { result } = renderHook(() => useImageAnalysis());

    await act(async () => {
      await result.current.analyzeImage(makeFile());
    });
    await waitFor(() => expect(result.current.result).not.toBeNull());

    act(() => {
      result.current.reset();
    });

    expect(result.current.result).toBeNull();
    expect(result.current.previewUrl).toBeNull();
    expect(result.current.error).toBeNull();
  });
});

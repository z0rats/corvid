import { act, renderHook, waitFor } from '@testing-library/react';
import { useImageMetadataRemoval } from './useImageMetadataRemoval';
import { imageMetadataRemovalApi } from '../../services/api/imageMetadataRemovalApi';
import { imageUtils } from '../../utils/imageUtils';

vi.mock('../../services/api/imageMetadataRemovalApi');
vi.mock('../../utils/imageUtils', () => ({
  imageUtils: { downloadBlob: vi.fn() },
}));

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('useImageMetadataRemoval', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no error and not loading', () => {
    const { result } = renderHook(() => useImageMetadataRemoval());

    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.success).toBe(false);
  });

  it('triggers a download on success', async () => {
    const blob = new Blob(['cleaned bytes'], { type: 'image/jpeg' });
    imageMetadataRemovalApi.removeMetadata.mockResolvedValue({ blob, filename: 'photo_cleaned.jpg' });

    const { result } = renderHook(() => useImageMetadataRemoval());

    await act(async () => {
      await result.current.removeMetadata(makeFile(), 'all');
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(imageUtils.downloadBlob).toHaveBeenCalledWith(blob, 'photo_cleaned.jpg');
    expect(result.current.success).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('passes the selected mode through to the API', async () => {
    imageMetadataRemovalApi.removeMetadata.mockResolvedValue({ blob: new Blob([]), filename: 'x.jpg' });

    const { result } = renderHook(() => useImageMetadataRemoval());
    const file = makeFile();

    await act(async () => {
      await result.current.removeMetadata(file, 'location_only');
    });

    expect(imageMetadataRemovalApi.removeMetadata).toHaveBeenCalledWith(file, 'location_only');
  });

  it('surfaces a plain error message on failure', async () => {
    imageMetadataRemovalApi.removeMetadata.mockRejectedValue({
      response: { data: { detail: 'Metadata removal failed' } },
    });

    const { result } = renderHook(() => useImageMetadataRemoval());

    await act(async () => {
      await result.current.removeMetadata(makeFile(), 'all');
    });

    expect(result.current.error).toBe('Metadata removal failed');
    expect(result.current.success).toBe(false);
  });

  it('parses the detail message out of a JSON error blob (responseType: blob gotcha)', async () => {
    const errorBlob = new Blob([JSON.stringify({ detail: 'Not a valid JPEG file' })], { type: 'application/json' });
    imageMetadataRemovalApi.removeMetadata.mockRejectedValue({
      response: { data: errorBlob },
      message: 'Request failed',
    });

    const { result } = renderHook(() => useImageMetadataRemoval());

    await act(async () => {
      await result.current.removeMetadata(makeFile(), 'all');
    });

    expect(result.current.error).toBe('Not a valid JPEG file');
  });
});

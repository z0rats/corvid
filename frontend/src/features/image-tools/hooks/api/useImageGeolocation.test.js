import { createElement } from 'react';
import { act, renderHook, waitFor } from '@testing-library/react';
import { createStore, Provider } from 'jotai';
import { useImageGeolocation } from './useImageGeolocation';
import { imageGeolocationApi } from '../../services/api/imageGeolocationApi';
import { apiKeysState } from '../../../../core/state/atoms';

vi.mock('../../services/api/imageGeolocationApi');

function renderImageGeolocationHook(apiKeys = { openai: 'sk-test' }) {
  const store = createStore();
  store.set(apiKeysState, apiKeys);
  return renderHook(() => useImageGeolocation(), {
    wrapper: ({ children }) => createElement(Provider, { store }, children),
  });
}

function makeFile() {
  return new File(['fake image content'], 'street.jpg', { type: 'image/jpeg' });
}

describe('useImageGeolocation', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('reports hasLlmKey as false when no LLM API key is configured', () => {
    const { result } = renderImageGeolocationHook({});

    expect(result.current.hasLlmKey).toBe(false);
  });

  it('reports hasLlmKey as true when an LLM API key is configured', () => {
    const { result } = renderImageGeolocationHook();

    expect(result.current.hasLlmKey).toBe(true);
  });

  it('starts with no result and no error', () => {
    const { result } = renderImageGeolocationHook();

    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('populates the result on a successful analysis', async () => {
    const mockResult = {
      candidates: [{ location: 'Serbia', confidence: 0.6, reasoning: 'road markings + signage' }],
      clues: [{ category: 'signage_language', observation: 'Cyrillic text', supports: 'Serbia/Balkans' }],
      caveats: 'Hypothesis only.',
      model_used: 'claude-sonnet-4-6',
    };
    imageGeolocationApi.geolocateImage.mockResolvedValue(mockResult);

    const { result } = renderImageGeolocationHook();

    await act(async () => {
      await result.current.geolocateImage(makeFile());
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.result).toEqual(mockResult);
    expect(result.current.error).toBeNull();
    expect(imageGeolocationApi.geolocateImage).toHaveBeenCalledTimes(1);
  });

  it('surfaces the API error message on failure', async () => {
    imageGeolocationApi.geolocateImage.mockRejectedValue({
      response: { data: { detail: 'No LLM models available (no API keys configured)' } },
    });

    const { result } = renderImageGeolocationHook();

    await act(async () => {
      await result.current.geolocateImage(makeFile());
    });

    expect(result.current.error).toBe('No LLM models available (no API keys configured)');
    expect(result.current.result).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});

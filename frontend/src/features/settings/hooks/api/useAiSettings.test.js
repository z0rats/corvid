import React from 'react';
import { act, renderHook } from '@testing-library/react';
import { createStore, Provider } from 'jotai';
import { useAiSettings } from './useAiSettings';
import { availableLlmModelsState } from '../../../../core/state/atoms';
import { LLM_MODELS_REPROBE_EVENT } from '../../../../core/utils/llmModelsReprobe';
import { settingsApi } from '../../services/api/settingsApi';

vi.mock('../../services/api/settingsApi');

afterEach(() => vi.clearAllMocks());

function withStore(store) {
  return function StoreWrapper({ children }) {
    return React.createElement(Provider, { store }, children);
  };
}

describe('useAiSettings — available models', () => {
  it('serves the app-wide registry list rather than fetching its own copy', () => {
    const store = createStore();
    const models = [{ id: 'ollama:llava', name: 'llava', provider: 'Ollama (local)' }];
    store.set(availableLlmModelsState, models);

    const { result } = renderHook(() => useAiSettings(), { wrapper: withStore(store) });

    expect(result.current.availableModels).toEqual(models);
  });

  it('asks the app-wide probe to refresh the list when the screen opens', () => {
    const listener = vi.fn();
    window.addEventListener(LLM_MODELS_REPROBE_EVENT, listener);

    renderHook(() => useAiSettings());

    window.removeEventListener(LLM_MODELS_REPROBE_EVENT, listener);
    expect(listener).toHaveBeenCalledTimes(1);
  });
});

describe('useAiSettings — updateAiSettings', () => {
  it('updates settings and returns a success message', async () => {
    settingsApi.updateAiSettings.mockResolvedValue({ defaultModel: 'claude' });
    const { result } = renderHook(() => useAiSettings());

    let returned;
    await act(async () => {
      returned = await result.current.updateAiSettings({ defaultModel: 'claude' });
    });

    expect(settingsApi.updateAiSettings).toHaveBeenCalledWith({ defaultModel: 'claude' });
    expect(returned).toMatchObject({ success: true });
    expect(result.current.loading).toBe(false);
  });

  it('prefers the response detail message on failure', async () => {
    settingsApi.updateAiSettings.mockRejectedValue({ response: { data: { detail: 'Invalid model' } } });
    const { result } = renderHook(() => useAiSettings());

    let returned;
    await act(async () => {
      returned = await result.current.updateAiSettings({ defaultModel: 'bad' });
    });

    expect(returned).toEqual({ success: false, message: 'Invalid model' });
    expect(result.current.loading).toBe(false);
  });

  it('falls back to the generic save-error message', async () => {
    settingsApi.updateAiSettings.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useAiSettings());

    let returned;
    await act(async () => {
      returned = await result.current.updateAiSettings({});
    });

    expect(returned).toEqual({ success: false, message: 'Failed to save changes.' });
  });
});

import { act, renderHook, waitFor } from '@testing-library/react';
import { createStore, Provider } from 'jotai';
import React from 'react';
import { apiKeysState, availableLlmModelsState, llmAvailableAtom, hasAnyLlmModelState } from '../../state/atoms';
import { useAppSettings, LLM_REPROBE_MIN_INTERVAL_MS } from './useAppSettings';
import { requestLlmModelsReprobe } from '../../utils/llmModelsReprobe';

vi.mock('../../services/api/settingsService', () => ({
  settingsService: {
    getApiKeys: vi.fn(),
    getModules: vi.fn(),
    getGeneralSettings: vi.fn(),
    getAiSettings: vi.fn(),
    getAvailableModels: vi.fn(),
  },
}));
vi.mock('../../i18n', () => ({ default: { changeLanguage: vi.fn() }, SUPPORTED_LANGUAGES: ['en'] }));

import { settingsService } from '../../services/api/settingsService';

function mountHook() {
  const store = createStore();
  const wrapper = ({ children }) => React.createElement(Provider, { store }, children);
  renderHook(() => useAppSettings(), { wrapper });
  return store;
}

beforeEach(() => {
  settingsService.getApiKeys.mockResolvedValue({});
  settingsService.getModules.mockResolvedValue([]);
  settingsService.getGeneralSettings.mockResolvedValue({ language: 'en' });
  settingsService.getAiSettings.mockResolvedValue({});
});

describe('useAppSettings LLM availability', () => {
  it('enables LLM features when an Ollama model is available and no key is set', async () => {
    settingsService.getAvailableModels.mockResolvedValue({
      models: [{ id: 'ollama:qwen2.5vl:7b', name: 'qwen2.5vl:7b', provider: 'Ollama (local)' }],
    });

    const store = mountHook();

    await waitFor(() => expect(store.get(hasAnyLlmModelState)).toBe(true));
    expect(store.get(llmAvailableAtom)).toBe(true);
  });

  it('enables LLM features for any registry model, not only Ollama ones', async () => {
    settingsService.getAvailableModels.mockResolvedValue({
      models: [{ id: 'gpt-5', name: 'GPT-5', provider: 'OpenAI' }],
    });

    const store = mountHook();

    await waitFor(() => expect(store.get(llmAvailableAtom)).toBe(true));
  });

  it('stays false when the registry is empty', async () => {
    settingsService.getAvailableModels.mockResolvedValue({ models: [] });

    const store = mountHook();

    await waitFor(() => expect(settingsService.getAvailableModels).toHaveBeenCalled());
    expect(store.get(llmAvailableAtom)).toBe(false);
  });

  it('stays false, without breaking other settings, if the models request fails', async () => {
    settingsService.getAvailableModels.mockRejectedValue(new Error('boom'));
    settingsService.getApiKeys.mockResolvedValue({ openai: true });

    const store = mountHook();

    await waitFor(() => expect(store.get(llmAvailableAtom)).toBe(true));
    expect(store.get(hasAnyLlmModelState)).toBe(false);
  });

  it('re-probes on returning to the tab, so a model pulled later unlocks AI without a reload', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      settingsService.getAvailableModels.mockResolvedValueOnce({ models: [] });
      const store = mountHook();
      await waitFor(() => expect(settingsService.getAvailableModels).toHaveBeenCalledTimes(1));

      // Too soon after the last probe: throttled.
      document.dispatchEvent(new Event('visibilitychange'));
      expect(settingsService.getAvailableModels).toHaveBeenCalledTimes(1);

      settingsService.getAvailableModels.mockResolvedValue({ models: [{ id: 'ollama:llava', name: 'llava' }] });
      vi.advanceTimersByTime(LLM_REPROBE_MIN_INTERVAL_MS);
      document.dispatchEvent(new Event('visibilitychange'));

      await waitFor(() => expect(store.get(llmAvailableAtom)).toBe(true));
      expect(settingsService.getAvailableModels).toHaveBeenCalledTimes(2);
    } finally {
      vi.useRealTimers();
    }
  });

  it('re-probes as soon as an LLM provider key is saved, without waiting for a tab refocus', async () => {
    settingsService.getAvailableModels.mockResolvedValueOnce({ models: [] });
    const store = mountHook();
    await waitFor(() => expect(settingsService.getAvailableModels).toHaveBeenCalledTimes(1));

    const gpt = { id: 'gpt-5', name: 'GPT-5', provider: 'OpenAI' };
    settingsService.getAvailableModels.mockResolvedValue({ models: [gpt] });
    act(() => { store.set(apiKeysState, { openai: true }); });

    await waitFor(() => expect(store.get(availableLlmModelsState)).toEqual([gpt]));
    expect(settingsService.getAvailableModels).toHaveBeenCalledTimes(2);
  });

  it('probes the registry once on load, even when LLM keys are configured', async () => {
    settingsService.getApiKeys.mockResolvedValue({ openai: true });
    settingsService.getAvailableModels.mockResolvedValue({ models: [{ id: 'gpt-5', name: 'GPT-5', provider: 'OpenAI' }] });

    const store = mountHook();

    await waitFor(() => expect(store.get(apiKeysState)).toEqual({ openai: true }));
    await waitFor(() => expect(store.get(llmAvailableAtom)).toBe(true));
    expect(settingsService.getAvailableModels).toHaveBeenCalledTimes(1);
  });

  it('re-probes at once, bypassing the focus throttle, when a screen requests it', async () => {
    settingsService.getAvailableModels.mockResolvedValueOnce({ models: [] });
    const store = mountHook();
    await waitFor(() => expect(settingsService.getAvailableModels).toHaveBeenCalledTimes(1));

    const llava = { id: 'ollama:llava', name: 'llava', provider: 'Ollama (local)' };
    settingsService.getAvailableModels.mockResolvedValue({ models: [llava] });
    act(() => { requestLlmModelsReprobe(); });

    await waitFor(() => expect(store.get(availableLlmModelsState)).toEqual([llava]));
    expect(settingsService.getAvailableModels).toHaveBeenCalledTimes(2);
  });
});


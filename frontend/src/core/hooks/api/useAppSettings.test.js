import { renderHook, waitFor } from '@testing-library/react';
import { createStore, Provider } from 'jotai';
import React from 'react';
import { hasLlmKeyAtom, hasLocalLlmState } from '../../state/atoms';
import { useAppSettings } from './useAppSettings';

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

describe('useAppSettings local LLM detection', () => {
  it('enables LLM features when an Ollama model is available and no key is set', async () => {
    settingsService.getAvailableModels.mockResolvedValue({
      models: [{ id: 'ollama:qwen2.5vl:7b', name: 'qwen2.5vl:7b', provider: 'Ollama (local)' }],
    });

    const store = mountHook();

    await waitFor(() => expect(store.get(hasLocalLlmState)).toBe(true));
    expect(store.get(hasLlmKeyAtom)).toBe(true);
  });

  it('does not treat provider-key models as local', async () => {
    settingsService.getAvailableModels.mockResolvedValue({
      models: [{ id: 'gpt-5', name: 'GPT-5', provider: 'OpenAI' }],
    });

    const store = mountHook();

    await waitFor(() => expect(settingsService.getAvailableModels).toHaveBeenCalled());
    expect(store.get(hasLocalLlmState)).toBe(false);
  });

  it('stays false, without breaking other settings, if the models request fails', async () => {
    settingsService.getAvailableModels.mockRejectedValue(new Error('boom'));
    settingsService.getApiKeys.mockResolvedValue({ openai: true });

    const store = mountHook();

    await waitFor(() => expect(store.get(hasLlmKeyAtom)).toBe(true));
    expect(store.get(hasLocalLlmState)).toBe(false);
  });
});

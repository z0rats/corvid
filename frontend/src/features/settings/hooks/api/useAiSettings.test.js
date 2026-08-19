import { act, renderHook, waitFor } from '@testing-library/react';
import { useAiSettings } from './useAiSettings';
import { settingsApi } from '../../services/api/settingsApi';

vi.mock('../../services/api/settingsApi');

afterEach(() => vi.clearAllMocks());

describe('useAiSettings — available models', () => {
  it('loads available models on mount', async () => {
    settingsApi.getAvailableModels.mockResolvedValue({ models: ['gpt-4', 'claude'] });

    const { result } = renderHook(() => useAiSettings());

    await waitFor(() => expect(result.current.availableModels).toEqual(['gpt-4', 'claude']));
  });

  it('falls back to an empty list when the models response has none', async () => {
    settingsApi.getAvailableModels.mockResolvedValue({});

    const { result } = renderHook(() => useAiSettings());

    await waitFor(() => expect(settingsApi.getAvailableModels).toHaveBeenCalled());
    expect(result.current.availableModels).toEqual([]);
  });

  it('falls back to an empty list when loading models fails', async () => {
    settingsApi.getAvailableModels.mockRejectedValue(new Error('down'));

    const { result } = renderHook(() => useAiSettings());

    await waitFor(() => expect(settingsApi.getAvailableModels).toHaveBeenCalled());
    expect(result.current.availableModels).toEqual([]);
  });
});

describe('useAiSettings — updateAiSettings', () => {
  it('updates settings and returns a success message', async () => {
    settingsApi.getAvailableModels.mockResolvedValue({ models: [] });
    settingsApi.updateAiSettings.mockResolvedValue({ defaultModel: 'claude' });
    const { result } = renderHook(() => useAiSettings());
    await waitFor(() => expect(settingsApi.getAvailableModels).toHaveBeenCalled());

    let returned;
    await act(async () => {
      returned = await result.current.updateAiSettings({ defaultModel: 'claude' });
    });

    expect(settingsApi.updateAiSettings).toHaveBeenCalledWith({ defaultModel: 'claude' });
    expect(returned).toMatchObject({ success: true });
    expect(result.current.loading).toBe(false);
  });

  it('prefers the response detail message on failure', async () => {
    settingsApi.getAvailableModels.mockResolvedValue({ models: [] });
    settingsApi.updateAiSettings.mockRejectedValue({ response: { data: { detail: 'Invalid model' } } });
    const { result } = renderHook(() => useAiSettings());
    await waitFor(() => expect(settingsApi.getAvailableModels).toHaveBeenCalled());

    let returned;
    await act(async () => {
      returned = await result.current.updateAiSettings({ defaultModel: 'bad' });
    });

    expect(returned).toEqual({ success: false, message: 'Invalid model' });
    expect(result.current.loading).toBe(false);
  });

  it('falls back to the generic save-error message', async () => {
    settingsApi.getAvailableModels.mockResolvedValue({ models: [] });
    settingsApi.updateAiSettings.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useAiSettings());
    await waitFor(() => expect(settingsApi.getAvailableModels).toHaveBeenCalled());

    let returned;
    await act(async () => {
      returned = await result.current.updateAiSettings({});
    });

    expect(returned).toEqual({ success: false, message: 'Failed to save changes.' });
  });
});

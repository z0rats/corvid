import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useCommandPaletteSettings } from './useCommandPaletteSettings';
import { settingsApi } from '../../services/api/settingsApi';
import { generalSettingsState } from '../../../../core/state/atoms';

vi.mock('../../services/api/settingsApi');

function resetGeneralSettings() {
  const { result } = renderHook(() => useSetAtom(generalSettingsState));
  act(() => result.current({}));
}

beforeEach(resetGeneralSettings);
afterEach(() => vi.clearAllMocks());

describe('useCommandPaletteSettings — updateCommandPaletteSettings', () => {
  it('sends the update and merges the response into generalSettingsState', async () => {
    settingsApi.updateCommandPaletteSettings.mockResolvedValue({ autoOpenOnSingleMatch: true });
    const { result } = renderHook(() => useCommandPaletteSettings());

    let returned;
    await act(async () => {
      returned = await result.current.updateCommandPaletteSettings({ autoOpenOnSingleMatch: true });
    });

    expect(settingsApi.updateCommandPaletteSettings).toHaveBeenCalledWith({ autoOpenOnSingleMatch: true });
    expect(returned).toMatchObject({
      success: true,
      message: 'Command palette settings updated successfully.',
    });
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('surfaces the save-error message on failure', async () => {
    settingsApi.updateCommandPaletteSettings.mockRejectedValue(new Error('down'));
    const { result } = renderHook(() => useCommandPaletteSettings());

    await act(async () => { await result.current.updateCommandPaletteSettings({}); });

    expect(result.current.error).toBe('Failed to save changes.');
  });
});

import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useGeneralSettings } from './useGeneralSettings';
import { settingsApi } from '../../services/api/settingsApi';
import { generalSettingsState } from '../../../../core/state/atoms';
import i18n from '../../../../core/i18n';

vi.mock('../../services/api/settingsApi');

function resetGeneralSettings() {
  const { result } = renderHook(() => useSetAtom(generalSettingsState));
  act(() => result.current({}));
}

beforeEach(resetGeneralSettings);
afterEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('en');
});

describe('useGeneralSettings — updateLanguage', () => {
  it('sends the update and switches the active i18n language', async () => {
    settingsApi.updateLanguage.mockResolvedValue({});
    const { result } = renderHook(() => useGeneralSettings());

    let returned;
    await act(async () => { returned = await result.current.updateLanguage('ru'); });

    expect(settingsApi.updateLanguage).toHaveBeenCalledWith('ru');
    expect(i18n.language).toBe('ru');
    expect(returned).toMatchObject({ success: true, message: 'Language updated successfully.' });
  });

  it('does not switch the active language on failure', async () => {
    settingsApi.updateLanguage.mockRejectedValue(new Error('down'));
    const { result } = renderHook(() => useGeneralSettings());

    await act(async () => { await result.current.updateLanguage('ru'); });

    expect(i18n.language).toBe('en');
    expect(result.current.error).toBe('Failed to save changes.');
  });
});

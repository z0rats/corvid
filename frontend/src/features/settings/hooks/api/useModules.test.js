import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useModules } from './useModules';
import { settingsApi } from '../../services/api/settingsApi';
import { modulesState } from '../../../../core/state/atoms';

vi.mock('../../services/api/settingsApi');

function resetModules() {
  const { result } = renderHook(() => useSetAtom(modulesState));
  act(() => result.current({}));
}

beforeEach(resetModules);
afterEach(() => vi.clearAllMocks());

describe('useModules — toggleModule', () => {
  it('enables a currently-disabled module', async () => {
    settingsApi.updateModuleStatus.mockResolvedValue({});
    const { result } = renderHook(() => useModules());

    let returned;
    await act(async () => { returned = await result.current.toggleModule('newsfeed', false); });

    expect(settingsApi.updateModuleStatus).toHaveBeenCalledWith('newsfeed', true);
    expect(returned).toEqual({ success: true, message: 'Module enabled successfully.' });
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('disables a currently-enabled module', async () => {
    settingsApi.updateModuleStatus.mockResolvedValue({});
    const { result } = renderHook(() => useModules());

    let returned;
    await act(async () => { returned = await result.current.toggleModule('newsfeed', true); });

    expect(settingsApi.updateModuleStatus).toHaveBeenCalledWith('newsfeed', false);
    expect(returned.message).toBe('Module disabled successfully.');
  });

  it('prefers the response detail message on failure', async () => {
    settingsApi.updateModuleStatus.mockRejectedValue({ response: { data: { detail: 'Locked' } } });
    const { result } = renderHook(() => useModules());

    let returned;
    await act(async () => { returned = await result.current.toggleModule('newsfeed', false); });

    expect(returned).toEqual({ success: false, message: 'Locked' });
    expect(result.current.error).toBe('Locked');
    expect(result.current.loading).toBe(false);
  });

  it('falls back to the generic save-error message', async () => {
    settingsApi.updateModuleStatus.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useModules());

    await act(async () => { await result.current.toggleModule('newsfeed', false); });

    expect(result.current.error).toBe('Failed to save changes.');
  });
});

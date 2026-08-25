import { act, renderHook } from '@testing-library/react';
import { useBackup } from './useBackup';
import { settingsApi } from '../../services/api/settingsApi';

vi.mock('../../services/api/settingsApi');

afterEach(() => vi.clearAllMocks());

describe('useBackup — getStatus', () => {
  it('delegates to settingsApi.getBackupStatus', async () => {
    settingsApi.getBackupStatus.mockResolvedValue({ supported: true, db_dialect: 'sqlite' });
    const { result } = renderHook(() => useBackup());

    const status = await result.current.getStatus();

    expect(status).toEqual({ supported: true, db_dialect: 'sqlite' });
  });
});

describe('useBackup — exportBackup', () => {
  it('returns the blob and filename on success', async () => {
    settingsApi.exportBackup.mockResolvedValue({ blob: 'BLOB', filename: 'backup.tar.gz' });
    const { result } = renderHook(() => useBackup());

    let returned;
    await act(async () => {
      returned = await result.current.exportBackup(
        { includeAccessToken: false, passphrase: null },
        'fallback'
      );
    });

    expect(returned).toEqual({ success: true, blob: 'BLOB', filename: 'backup.tar.gz' });
  });

  it('surfaces the error message on failure', async () => {
    settingsApi.exportBackup.mockRejectedValue(new Error('No encryption key file found'));
    const { result } = renderHook(() => useBackup());

    let returned;
    await act(async () => {
      returned = await result.current.exportBackup(
        { includeAccessToken: false, passphrase: null },
        'fallback'
      );
    });

    expect(returned).toEqual({ success: false, message: 'No encryption key file found' });
  });

  it('falls back to the given message when the error has none', async () => {
    settingsApi.exportBackup.mockRejectedValue({});
    const { result } = renderHook(() => useBackup());

    let returned;
    await act(async () => {
      returned = await result.current.exportBackup(
        { includeAccessToken: false, passphrase: null },
        'fallback'
      );
    });

    expect(returned).toEqual({ success: false, message: 'fallback' });
  });

  it('toggles the exporting flag around the call', async () => {
    let resolvePromise;
    settingsApi.exportBackup.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      })
    );
    const { result } = renderHook(() => useBackup());

    let callPromise;
    act(() => {
      callPromise = result.current.exportBackup(
        { includeAccessToken: false, passphrase: null },
        'fallback'
      );
    });
    expect(result.current.exporting).toBe(true);

    await act(async () => {
      resolvePromise({ blob: 'x', filename: 'y' });
      await callPromise;
    });
    expect(result.current.exporting).toBe(false);
  });
});

describe('useBackup — restoreBackup', () => {
  it('returns success result including access_token_restored', async () => {
    settingsApi.restoreBackup.mockResolvedValue({ restart_required: true, access_token_restored: true });
    const { result } = renderHook(() => useBackup());

    let returned;
    await act(async () => {
      returned = await result.current.restoreBackup({ file: {}, passphrase: null }, 'fallback');
    });

    expect(returned).toEqual({ success: true, restart_required: true, access_token_restored: true });
  });

  it('surfaces the API error detail on failure', async () => {
    settingsApi.restoreBackup.mockRejectedValue({
      response: { data: { detail: 'Incorrect passphrase' } },
    });
    const { result } = renderHook(() => useBackup());

    let returned;
    await act(async () => {
      returned = await result.current.restoreBackup({ file: {}, passphrase: 'wrong' }, 'fallback');
    });

    expect(returned).toEqual({ success: false, message: 'Incorrect passphrase' });
  });

  it('toggles the restoring flag around the call', async () => {
    let resolvePromise;
    settingsApi.restoreBackup.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      })
    );
    const { result } = renderHook(() => useBackup());

    let callPromise;
    act(() => {
      callPromise = result.current.restoreBackup({ file: {}, passphrase: null }, 'fallback');
    });
    expect(result.current.restoring).toBe(true);

    await act(async () => {
      resolvePromise({ restart_required: true, access_token_restored: false });
      await callPromise;
    });
    expect(result.current.restoring).toBe(false);
  });
});

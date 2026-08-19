import { renderHook, waitFor } from '@testing-library/react';
import { useBulkLookupSettings } from './useBulkLookupSettings';
import { iocLookupApi } from '../../../../shared/services/api/iocLookupApi';

vi.mock('../../../../shared/services/api/iocLookupApi');

afterEach(() => vi.clearAllMocks());

const serviceDefinitions = {
  abuseipdb: { isAvailable: true, requiredKeys: ['abuseipdb'] },
  virustotal: { isAvailable: true, requiredKeys: ['virustotal'] },
  blacklist: { isAvailable: true, requiredKeys: [] }, // keyless service
  disabled_service: { isAvailable: false, requiredKeys: [] },
};

describe('useBulkLookupSettings', () => {
  it('does not fetch while service definitions are still loading', () => {
    renderHook(() => useBulkLookupSettings({}, true));
    expect(iocLookupApi.fetchBulkLookupSettings).not.toHaveBeenCalled();
  });

  it('does not fetch when there are no service definitions yet', () => {
    renderHook(() => useBulkLookupSettings({}, false));
    expect(iocLookupApi.fetchBulkLookupSettings).not.toHaveBeenCalled();
  });

  it('marks a keyed service enabled only when its required key is present', async () => {
    iocLookupApi.fetchBulkLookupSettings.mockResolvedValue({ abuseipdb: true, virustotal: false });
    const { result } = renderHook(() => useBulkLookupSettings(serviceDefinitions, false));

    await waitFor(() => expect(result.current.loadingSettings).toBe(false));

    const byName = Object.fromEntries(result.current.serviceSettings.map((s) => [s.name, s]));
    expect(byName.abuseipdb.is_bulk_lookup_enabled).toBe(true);
    expect(byName.virustotal.is_bulk_lookup_enabled).toBe(false);
  });

  it('treats a keyless service as enabled only when explicitly true in the status map', async () => {
    iocLookupApi.fetchBulkLookupSettings.mockResolvedValue({ blacklist: true });
    const { result } = renderHook(() => useBulkLookupSettings(serviceDefinitions, false));

    await waitFor(() => expect(result.current.loadingSettings).toBe(false));

    const byName = Object.fromEntries(result.current.serviceSettings.map((s) => [s.name, s]));
    expect(byName.blacklist.is_bulk_lookup_enabled).toBe(true);
  });

  it('excludes services marked unavailable in their definition', async () => {
    iocLookupApi.fetchBulkLookupSettings.mockResolvedValue({});
    const { result } = renderHook(() => useBulkLookupSettings(serviceDefinitions, false));

    await waitFor(() => expect(result.current.loadingSettings).toBe(false));

    expect(result.current.serviceSettings.map((s) => s.name)).not.toContain('disabled_service');
  });

  it('hasEnabledServices/enabledServiceNames reflect the enabled subset', async () => {
    iocLookupApi.fetchBulkLookupSettings.mockResolvedValue({ abuseipdb: true, virustotal: false });
    const { result } = renderHook(() => useBulkLookupSettings(serviceDefinitions, false));

    await waitFor(() => expect(result.current.loadingSettings).toBe(false));

    expect(result.current.hasEnabledServices).toBe(true);
    expect(result.current.enabledServiceNames).toContain('abuseipdb');
    expect(result.current.enabledServiceNames).not.toContain('virustotal');
  });

  it('sets a settingsError and stops loading when the fetch fails', async () => {
    iocLookupApi.fetchBulkLookupSettings.mockRejectedValue(new Error('network down'));
    const { result } = renderHook(() => useBulkLookupSettings(serviceDefinitions, false));

    await waitFor(() => expect(result.current.loadingSettings).toBe(false));

    expect(result.current.settingsError).toBe('Could not load settings for bulk lookup services.');
  });

  it('refreshSettings re-fetches on demand', async () => {
    iocLookupApi.fetchBulkLookupSettings.mockResolvedValue({});
    const { result } = renderHook(() => useBulkLookupSettings(serviceDefinitions, false));
    await waitFor(() => expect(result.current.loadingSettings).toBe(false));
    iocLookupApi.fetchBulkLookupSettings.mockClear();

    await result.current.refreshSettings();

    expect(iocLookupApi.fetchBulkLookupSettings).toHaveBeenCalledTimes(1);
  });
});

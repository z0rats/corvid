import { renderHook } from '@testing-library/react';
import { useServiceFilter } from './useServiceFilter';
import { useServiceDefinitions } from './useServiceDefinitions';
import { SERVICE_DEFINITIONS } from '../config/serviceConfig';

vi.mock('./useServiceDefinitions');
vi.mock('../config/serviceConfig', () => ({ SERVICE_DEFINITIONS: {} }));

afterEach(() => {
  Object.keys(SERVICE_DEFINITIONS).forEach((key) => delete SERVICE_DEFINITIONS[key]);
  vi.clearAllMocks();
});

describe('useServiceFilter', () => {
  it('returns externallyFilteredServices unchanged when given, bypassing all filtering', () => {
    useServiceDefinitions.mockReturnValue({ serviceDefinitions: {}, loading: false });
    const external = [{ key: 'x' }];

    const { result } = renderHook(() => useServiceFilter('IPv4', external));

    expect(result.current).toBe(external);
  });

  it('returns an empty list while service definitions are loading', () => {
    useServiceDefinitions.mockReturnValue({ serviceDefinitions: {}, loading: true });

    const { result } = renderHook(() => useServiceFilter('IPv4', null));

    expect(result.current).toEqual([]);
  });

  it('returns an empty list when no iocType is given', () => {
    useServiceDefinitions.mockReturnValue({
      serviceDefinitions: { abuseipdb: { supportedIocTypes: ['IPv4'], isAvailable: true } },
      loading: false,
    });

    const { result } = renderHook(() => useServiceFilter(null, null));

    expect(result.current).toEqual([]);
  });

  it('filters to services supporting the given ioc type and marked available', () => {
    useServiceDefinitions.mockReturnValue({
      serviceDefinitions: {
        abuseipdb: { supportedIocTypes: ['IPv4'], isAvailable: true },
        virustotal: { supportedIocTypes: ['Domain'], isAvailable: true },
        maltiverse: { supportedIocTypes: ['IPv4'], isAvailable: false },
      },
      loading: false,
    });

    const { result } = renderHook(() => useServiceFilter('IPv4', null));

    expect(result.current.map((s) => s.key)).toEqual(['abuseipdb']);
  });

  it('merges in the frontend detailComponent/getSummaryAndTlp/icon from SERVICE_DEFINITIONS', () => {
    const getSummaryAndTlp = () => ({});
    SERVICE_DEFINITIONS.abuseipdb = { detailComponent: 'AbuseIpdbDetails', getSummaryAndTlp, icon: 'aipdb' };
    useServiceDefinitions.mockReturnValue({
      serviceDefinitions: { abuseipdb: { supportedIocTypes: ['IPv4'], isAvailable: true } },
      loading: false,
    });

    const { result } = renderHook(() => useServiceFilter('IPv4', null));

    expect(result.current[0]).toMatchObject({
      detailComponent: 'AbuseIpdbDetails',
      getSummaryAndTlp,
      icon: 'aipdb',
    });
  });

  it('falls back to the service key as its display name when the backend gives none', () => {
    useServiceDefinitions.mockReturnValue({
      serviceDefinitions: { abuseipdb: { supportedIocTypes: ['IPv4'], isAvailable: true } },
      loading: false,
    });

    const { result } = renderHook(() => useServiceFilter('IPv4', null));

    expect(result.current[0].name).toBe('abuseipdb');
  });

  it('builds a working lookupEndpoint URL for the service/ioc/iocType', () => {
    useServiceDefinitions.mockReturnValue({
      serviceDefinitions: { abuseipdb: { supportedIocTypes: ['IPv4'], isAvailable: true } },
      loading: false,
    });

    const { result } = renderHook(() => useServiceFilter('IPv4', null));

    expect(result.current[0].lookupEndpoint('1.2.3.4', 'IPv4')).toBe(
      '/api/ioc/lookup/abuseipdb?ioc=1.2.3.4&ioc_type=IPv4',
    );
  });
});

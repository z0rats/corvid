import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useBulkLookupProcessor } from './useBulkLookupProcessor';
import { bulkLookupStateAtom, BULK_LOOKUP_INITIAL_STATE } from '../state/bulkLookupAtoms';
import { determineIocType } from '../../shared/utils/iocDefinitions';
import { SERVICE_DEFINITIONS } from '../../shared/config/serviceConfig';
import { iocLookupApi } from '../../../shared/services/api/iocLookupApi';

vi.mock('../../shared/utils/iocDefinitions', () => ({
  determineIocType: vi.fn(),
  IOC_TYPES: {
    IPV4: 'ipv4', IPV6: 'ipv6', DOMAIN: 'domain', URL: 'url',
    MD5: 'md5', SHA1: 'sha1', SHA256: 'sha256', EMAIL: 'email', CVE: 'cve', UNKNOWN: 'unknown',
  },
}));
vi.mock('../../shared/utils/tlpUtils', () => ({ getOverallTlp: vi.fn(() => 'WHITE') }));
vi.mock('../../shared/config/serviceConfig', () => ({ SERVICE_DEFINITIONS: {} }));
vi.mock('../../../shared/services/api/iocLookupApi');

// bulkLookupStateAtom, and the module-scoped iocMap/activeAbortController the
// hook itself keeps, are shared across tests in this file - every test resets
// the atom explicitly, and performLookup's own iocMap.clear()/controller
// replacement keeps the module state self-contained per call.
function useTestHarness() {
  const processor = useBulkLookupProcessor();
  const setState = useSetAtom(bulkLookupStateAtom);
  return { ...processor, setState };
}

function encodeSseFrames(events) {
  return events.map((event) => `data: ${JSON.stringify(event)}\n\n`);
}

function makeSseStream(frames) {
  const encoder = new TextEncoder();
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < frames.length) {
        controller.enqueue(encoder.encode(frames[i]));
        i += 1;
        return;
      }
      controller.close();
    },
  });
}

function makeBlockingStream() {
  return new ReadableStream({ pull() {} });
}

beforeEach(() => {
  determineIocType.mockImplementation((ioc) => (ioc.includes('.') ? 'ipv4' : 'unknown'));
});

afterEach(() => {
  Object.keys(SERVICE_DEFINITIONS).forEach((key) => delete SERVICE_DEFINITIONS[key]);
  vi.clearAllMocks();
});

describe('useBulkLookupProcessor — performLookup validation', () => {
  it('sets an error and does not call the API when no services are selected', async () => {
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    await act(async () => {
      await result.current.performLookup('1.2.3.4', []);
    });

    expect(result.current.processorError).toContain('select at least one service');
    expect(iocLookupApi.bulkLookup).not.toHaveBeenCalled();
  });

  it('sets an error when the input has no parseable IOCs', async () => {
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    await act(async () => {
      await result.current.performLookup('   ,  , ', ['abuseipdb']);
    });

    expect(result.current.processorError).toContain('at least one IOC');
    expect(result.current.loading).toBe(false);
  });
});

describe('useBulkLookupProcessor — performLookup happy path', () => {
  it('dedupes IOCs split on commas/spaces/newlines and calls bulkLookup with them', async () => {
    iocLookupApi.bulkLookup.mockResolvedValue(makeSseStream([]));
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    await act(async () => {
      await result.current.performLookup('1.2.3.4, 1.2.3.4\n5.6.7.8', ['abuseipdb']);
    });

    expect(iocLookupApi.bulkLookup).toHaveBeenCalledWith(['1.2.3.4', '5.6.7.8'], ['abuseipdb']);
  });

  it('categorizes each ioc by its determined type', async () => {
    iocLookupApi.bulkLookup.mockResolvedValue(makeSseStream([]));
    determineIocType.mockImplementation((ioc) => (ioc === '1.2.3.4' ? 'ipv4' : 'domain'));
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    await act(async () => {
      await result.current.performLookup('1.2.3.4, example.com', ['abuseipdb']);
    });

    expect(result.current.categorizedIocs.ipv4.map((i) => i.value)).toEqual(['1.2.3.4']);
    expect(result.current.categorizedIocs.domain.map((i) => i.value)).toEqual(['example.com']);
  });
});

describe('useBulkLookupProcessor — SSE stream processing', () => {
  it('applies a completed event using the service definition getSummaryAndTlp', async () => {
    SERVICE_DEFINITIONS.abuseipdb = {
      supportedIocTypes: ['ipv4'],
      getSummaryAndTlp: () => ({ summary: 'Malicious', tlp: 'RED', keyMetric: 90 }),
    };
    iocLookupApi.bulkLookup.mockResolvedValue(
      makeSseStream(encodeSseFrames([{ ioc: '1.2.3.4', service: 'abuseipdb', data: { score: 90 } }])),
    );
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    await act(async () => {
      await result.current.performLookup('1.2.3.4', ['abuseipdb']);
    });

    const entry = result.current.categorizedIocs.ipv4[0];
    expect(entry.services.abuseipdb).toMatchObject({ status: 'completed', summary: 'Malicious', tlp: 'RED' });
  });

  it('maps a "not found" error to a completed/GREEN entry', async () => {
    SERVICE_DEFINITIONS.abuseipdb = { supportedIocTypes: ['ipv4'], getSummaryAndTlp: () => ({}) };
    iocLookupApi.bulkLookup.mockResolvedValue(
      makeSseStream(
        encodeSseFrames([{ ioc: '1.2.3.4', service: 'abuseipdb', error: 'IOC not found in database' }]),
      ),
    );
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    await act(async () => {
      await result.current.performLookup('1.2.3.4', ['abuseipdb']);
    });

    const entry = result.current.categorizedIocs.ipv4[0];
    expect(entry.services.abuseipdb).toMatchObject({ status: 'completed', summary: 'Not found', tlp: 'GREEN' });
  });

  it('maps any other error to an error status', async () => {
    SERVICE_DEFINITIONS.abuseipdb = { supportedIocTypes: ['ipv4'], getSummaryAndTlp: () => ({}) };
    iocLookupApi.bulkLookup.mockResolvedValue(
      makeSseStream(encodeSseFrames([{ ioc: '1.2.3.4', service: 'abuseipdb', error: 'Rate limited' }])),
    );
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    await act(async () => {
      await result.current.performLookup('1.2.3.4', ['abuseipdb']);
    });

    const entry = result.current.categorizedIocs.ipv4[0];
    expect(entry.services.abuseipdb).toMatchObject({ status: 'error', summary: 'Rate limited' });
  });

  it('silently ignores an event for a service with no known definition', async () => {
    iocLookupApi.bulkLookup.mockResolvedValue(
      makeSseStream(encodeSseFrames([{ ioc: '1.2.3.4', service: 'unknown_service', data: {} }])),
    );
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    await expect(
      act(async () => {
        await result.current.performLookup('1.2.3.4', ['unknown_service']);
      }),
    ).resolves.not.toThrow();
  });
});

describe('useBulkLookupProcessor — connection failure', () => {
  it('sets a processorError and clears loading when the stream never opens', async () => {
    iocLookupApi.bulkLookup.mockRejectedValue(new Error('502 Bad Gateway'));
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    await act(async () => {
      await result.current.performLookup('1.2.3.4', ['abuseipdb']);
    });

    expect(result.current.processorError).toContain('502 Bad Gateway');
    expect(result.current.loading).toBe(false);
  });
});

describe('useBulkLookupProcessor — orderedIocTypes', () => {
  it('orders present types by the preferred order, appending any others at the end', async () => {
    iocLookupApi.bulkLookup.mockResolvedValue(makeSseStream([]));
    determineIocType.mockImplementation((ioc) => {
      if (ioc === 'a.com') return 'domain';
      if (ioc === '1.2.3.4') return 'ipv4';
      return 'unknown';
    });
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    await act(async () => {
      await result.current.performLookup('a.com, 1.2.3.4', ['abuseipdb']);
    });

    // ipv4 precedes domain in PREFERRED_IOC_ORDER even though domain appeared first in input.
    expect(result.current.orderedIocTypes).toEqual(['ipv4', 'domain']);
  });
});

describe('useBulkLookupProcessor — starting a new run supersedes an in-flight one', () => {
  it('replaces state with only the newer run\'s IOCs, not a mix of both', async () => {
    iocLookupApi.bulkLookup.mockImplementationOnce(async () => makeBlockingStream());
    const { result } = renderHook(() => useTestHarness());
    act(() => result.current.setState(BULK_LOOKUP_INITIAL_STATE));

    // First run never resolves (blocking stream) - deliberately not awaited,
    // same as starting it and immediately navigating away/re-running.
    act(() => {
      result.current.performLookup('1.2.3.4', ['abuseipdb']);
    });
    await act(async () => {
      await Promise.resolve();
    });

    iocLookupApi.bulkLookup.mockResolvedValueOnce(makeSseStream([]));
    await act(async () => {
      await result.current.performLookup('5.6.7.8', ['abuseipdb']);
    });

    const allValues = Object.values(result.current.categorizedIocs).flat().map((i) => i.value);
    expect(allValues).toEqual(['5.6.7.8']);
    expect(iocLookupApi.bulkLookup).toHaveBeenCalledTimes(2);
  });
});

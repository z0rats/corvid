import { act, renderHook } from '@testing-library/react';
import { useExtractor } from './useExtractor';
import { extractorApi } from '../../shared/services/api/extractorApi';

vi.mock('../../shared/services/api/extractorApi');

beforeEach(() => {
  Object.assign(navigator, { clipboard: { writeText: vi.fn().mockResolvedValue(undefined) } });
});

afterEach(() => vi.clearAllMocks());

describe('useExtractor — extractFromText', () => {
  it('stores the extracted data on success', async () => {
    const data = { domains: ['example.com'], statistics: { total_unique_iocs: 1 } };
    extractorApi.extractFromText.mockResolvedValue(data);
    const { result } = renderHook(() => useExtractor());

    await act(async () => {
      await result.current.extractFromText('example.com');
    });

    expect(extractorApi.extractFromText).toHaveBeenCalledWith('example.com');
    expect(result.current.extractedData).toEqual(data);
    expect(result.current.statistics).toEqual({ total_unique_iocs: 1 });
    expect(result.current.hasResults).toBe(true);
  });

  it('surfaces the error message and clears loading on failure', async () => {
    extractorApi.extractFromText.mockRejectedValue(new Error('server exploded'));
    const { result } = renderHook(() => useExtractor());

    let caught;
    await act(async () => {
      try {
        await result.current.extractFromText('x');
      } catch (err) {
        caught = err;
      }
    });

    expect(caught.message).toBe('server exploded');
    expect(result.current.error).toBe('server exploded');
    expect(result.current.isLoading).toBe(false);
  });
});

describe('useExtractor — extractFromFile', () => {
  it('throws immediately when no file is given', async () => {
    const { result } = renderHook(() => useExtractor());

    await expect(
      act(async () => {
        await result.current.extractFromFile(null);
      }),
    ).rejects.toThrow('No file provided');

    expect(extractorApi.extractFromFile).not.toHaveBeenCalled();
  });

  it('stores the extracted data and resets upload progress on success', async () => {
    const file = { name: 'iocs.txt', size: 10, type: 'text/plain' };
    const data = { domains: ['example.com'], statistics: { total_unique_iocs: 1 } };
    extractorApi.extractFromFile.mockResolvedValue(data);
    const { result } = renderHook(() => useExtractor());

    await act(async () => {
      await result.current.extractFromFile(file);
    });

    expect(result.current.extractedData).toEqual(data);
    expect(result.current.uploadProgress).toBe(0);
  });

  it('resets upload progress and rethrows on failure', async () => {
    const file = { name: 'iocs.txt', size: 10, type: 'text/plain' };
    extractorApi.extractFromFile.mockRejectedValue(new Error('upload failed'));
    const { result } = renderHook(() => useExtractor());

    await expect(
      act(async () => {
        await result.current.extractFromFile(file);
      }),
    ).rejects.toThrow('upload failed');

    expect(result.current.uploadProgress).toBe(0);
  });
});

describe('useExtractor — copyAllIOCs / exportAllIOCs', () => {
  it('copyAllIOCs collects and copies every IOC across categories', async () => {
    extractorApi.extractFromText.mockResolvedValue({ domains: ['a.com'], ips: ['1.2.3.4'] });
    const { result } = renderHook(() => useExtractor());
    await act(async () => {
      await result.current.extractFromText('x');
    });

    await act(async () => {
      await result.current.copyAllIOCs();
    });

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('a.com\n1.2.3.4');
  });

  it('exportAllIOCs throws when there is nothing extracted yet', () => {
    const { result } = renderHook(() => useExtractor());
    expect(() => result.current.exportAllIOCs()).toThrow('No IOCs to export');
  });
});

describe('useExtractor — reset', () => {
  it('clears extracted data, progress, and any error', async () => {
    extractorApi.extractFromText.mockResolvedValue({ domains: ['a.com'] });
    const { result } = renderHook(() => useExtractor());
    await act(async () => {
      await result.current.extractFromText('x');
    });

    act(() => result.current.reset());

    expect(result.current.extractedData).toBeNull();
    expect(result.current.uploadProgress).toBe(0);
    expect(result.current.error).toBeNull();
    expect(result.current.hasResults).toBe(false);
  });
});

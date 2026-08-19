import { collectAllIOCs, copyIOCsToClipboard, exportIOCsToFile, mapIocTypeToLabel } from './iocExportUtils';

describe('collectAllIOCs', () => {
  it('flattens every IOC category into a single array', () => {
    const data = {
      domains: ['example.com'],
      ips: ['1.2.3.4'],
      urls: ['https://example.com'],
      emails: ['a@example.com'],
      md5: ['abc'],
      sha1: [],
      sha256: [],
      cves: ['CVE-2024-1234'],
    };

    expect(collectAllIOCs(data)).toEqual([
      'example.com',
      '1.2.3.4',
      'https://example.com',
      'a@example.com',
      'abc',
      'CVE-2024-1234',
    ]);
  });

  it('returns an empty array when given no data', () => {
    expect(collectAllIOCs(null)).toEqual([]);
    expect(collectAllIOCs(undefined)).toEqual([]);
  });

  it('tolerates missing categories', () => {
    expect(collectAllIOCs({ domains: ['a.com'] })).toEqual(['a.com']);
  });
});

describe('copyIOCsToClipboard', () => {
  beforeEach(() => {
    Object.assign(navigator, { clipboard: { writeText: vi.fn().mockResolvedValue(undefined) } });
  });

  it('joins IOCs with newlines and copies them', async () => {
    const result = await copyIOCsToClipboard(['1.2.3.4', 'example.com']);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('1.2.3.4\nexample.com');
    expect(result).toEqual({ count: 2, message: 'Copied 2 IOCs to clipboard' });
  });

  it('throws when there is nothing to copy', async () => {
    await expect(copyIOCsToClipboard([])).rejects.toThrow('No IOCs to copy');
    await expect(copyIOCsToClipboard(null)).rejects.toThrow('No IOCs to copy');
  });
});

describe('exportIOCsToFile', () => {
  it('throws when there is nothing to export', () => {
    expect(() => exportIOCsToFile([])).toThrow('No IOCs to export');
  });

  it('creates an object URL, clicks a synthetic download link, then revokes the URL', () => {
    const createObjectURL = vi.fn().mockReturnValue('blob:fake-url');
    const revokeObjectURL = vi.fn();
    vi.stubGlobal('URL', { ...URL, createObjectURL, revokeObjectURL });
    // A real anchor (not a plain object) - the source appends it to
    // document.body, which requires an actual DOM node.
    const anchor = document.createElement('a');
    const clickSpy = vi.spyOn(anchor, 'click').mockImplementation(() => {});
    vi.spyOn(document, 'createElement').mockReturnValue(anchor);

    const result = exportIOCsToFile(['1.2.3.4'], 'my_iocs');

    expect(anchor.download).toMatch(/^my_iocs_\d{4}-\d{2}-\d{2}\.txt$/);
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:fake-url');
    expect(result).toEqual({ count: 1, message: 'Exported 1 IOCs to file' });

    document.createElement.mockRestore();
    vi.unstubAllGlobals();
  });
});

describe('mapIocTypeToLabel', () => {
  it('maps a known type to its display label', () => {
    expect(mapIocTypeToLabel('ipv4')).toBe('IPv4');
    expect(mapIocTypeToLabel('domain')).toBe('Domain');
  });

  it('falls back to MD5 for an unknown type', () => {
    // Documents the actual (possibly surprising) fallback behavior - any
    // unrecognized type label is displayed as "MD5", not a generic label.
    expect(mapIocTypeToLabel('not-a-real-type')).toBe('MD5');
  });
});

import { downloadBlob, round } from './fileUtils';

describe('round', () => {
  it('rounds to one decimal place', () => {
    expect(round(1.23)).toBe(1.2);
    expect(round(1.25)).toBe(1.3);
    expect(round(1.24)).toBe(1.2);
  });
});

describe('downloadBlob', () => {
  it('creates an object URL, clicks a synthetic download link, then revokes the URL', () => {
    const createObjectURL = vi.fn().mockReturnValue('blob:fake-url');
    const revokeObjectURL = vi.fn();
    vi.stubGlobal('URL', { ...URL, createObjectURL, revokeObjectURL });

    const clickSpy = vi.fn();
    const anchor = { click: clickSpy, href: '', download: '' };
    vi.spyOn(document, 'createElement').mockReturnValue(anchor);

    const blob = new Blob(['content']);
    downloadBlob(blob, 'report.json');

    expect(createObjectURL).toHaveBeenCalledWith(blob);
    expect(anchor.download).toBe('report.json');
    expect(anchor.href).toBe('blob:fake-url');
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:fake-url');

    document.createElement.mockRestore();
    vi.unstubAllGlobals();
  });
});

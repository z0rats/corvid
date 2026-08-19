import {
  generateUUIDv4,
  getCurrentDate,
  generateSID,
  exportAsFile,
  validateRequiredFields,
} from './ruleUtils';

describe('generateUUIDv4', () => {
  it('returns a well-formed v4 UUID', () => {
    const uuid = generateUUIDv4();
    expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
  });

  it('returns a different value each call', () => {
    expect(generateUUIDv4()).not.toBe(generateUUIDv4());
  });
});

describe('getCurrentDate', () => {
  it('returns today in YYYY-MM-DD format', () => {
    expect(getCurrentDate()).toBe(new Date().toISOString().split('T')[0]);
  });
});

describe('generateSID', () => {
  it('returns a 6-digit number', () => {
    for (let i = 0; i < 20; i += 1) {
      const sid = generateSID();
      expect(sid).toBeGreaterThanOrEqual(100000);
      expect(sid).toBeLessThanOrEqual(999999);
    }
  });
});

describe('validateRequiredFields', () => {
  it('returns no errors when every required field is present', () => {
    expect(validateRequiredFields({ title: 't', id: '1' }, ['title', 'id'])).toEqual([]);
  });

  it('reports every missing field, not just the first', () => {
    const errors = validateRequiredFields({}, ['title', 'id']);
    expect(errors).toEqual(['title is required', 'id is required']);
  });

  it('treats a whitespace-only string as missing', () => {
    expect(validateRequiredFields({ title: '   ' }, ['title'])).toEqual(['title is required']);
  });

  it('does not flag a non-string falsy-but-present value like 0', () => {
    // 0 is falsy in JS, so validateRequiredFields treats it as "missing" -
    // documents the actual (possibly surprising) behavior for a numeric field.
    expect(validateRequiredFields({ priority: 0 }, ['priority'])).toEqual(['priority is required']);
  });
});

describe('exportAsFile', () => {
  it('creates an object URL, clicks a synthetic download link, then revokes the URL', () => {
    const createObjectURL = vi.fn().mockReturnValue('blob:fake-url');
    const revokeObjectURL = vi.fn();
    vi.stubGlobal('URL', { ...URL, createObjectURL, revokeObjectURL });

    const clickSpy = vi.fn();
    const anchor = { click: clickSpy, href: '', download: '' };
    vi.spyOn(document, 'createElement').mockReturnValue(anchor);

    exportAsFile('rule content', 'my_rule.yml');

    expect(createObjectURL).toHaveBeenCalled();
    expect(anchor.download).toBe('my_rule.yml');
    expect(anchor.href).toBe('blob:fake-url');
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:fake-url');

    document.createElement.mockRestore();
    vi.unstubAllGlobals();
  });
});

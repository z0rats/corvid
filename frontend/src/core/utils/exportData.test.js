import { toCsv, exportFileName } from './exportData';

describe('toCsv', () => {
  it('uses the union of keys as columns, in first-seen order', () => {
    expect(toCsv([{ a: 1, b: 2 }, { b: 3, c: 4 }])).toBe('a,b,c\r\n1,2,\r\n,3,4\r\n');
  });

  it('quotes commas, quotes and newlines', () => {
    expect(toCsv([{ v: 'a,b' }, { v: 'say "hi"' }, { v: 'x\ny' }]))
      .toBe('v\r\n"a,b"\r\n"say ""hi"""\r\n"x\ny"\r\n');
  });

  it('serializes nested values as JSON', () => {
    expect(toCsv([{ tags: ['x', 'y'] }])).toBe('tags\r\n"[""x"",""y""]"\r\n');
  });

  it('neutralizes spreadsheet formulas from scanned content', () => {
    expect(toCsv([{ v: '=HYPERLINK("http://evil")' }, { v: '-2+3' }, { v: '@SUM(A1)' }]))
      .toBe('v\r\n"\'=HYPERLINK(""http://evil"")"\r\n\'-2+3\r\n\'@SUM(A1)\r\n');
  });

  it('leaves null/undefined cells empty', () => {
    expect(toCsv([{ a: null, b: undefined, c: 0 }])).toBe('a,b,c\r\n,,0\r\n');
  });
});

describe('exportFileName', () => {
  it('joins parts and strips unsafe characters', () => {
    expect(exportFileName('reddit-search', 'u/some user', 3)).toBe('reddit-search-u_some_user-3');
    expect(exportFileName('amass', 'example.com', null)).toBe('amass-example.com');
  });
});

import yaml from 'js-yaml';
import {
  generateSigmaRule,
  createInitialMetadata,
  createInitialLogSource,
  createInitialDetection,
  yamlScalar,
  buildSigmaCondition,
} from './sigmaRuleService';

function _metadata(overrides = {}) {
  return {
    title: 'Suspicious PowerShell',
    id: 'abc-123',
    status: 'Experimental',
    description: '',
    authors: [],
    date: '',
    modified: '',
    license: '',
    level: 'High',
    ...overrides,
  };
}

const item = (value) => ({ id: value, value });
const cond = (field, modifier, value) => ({ id: `${field}${value}`, field, modifier, value });
const emptyLogSource = { product: '', category: '', service: '', definition: '' };
const detections = (overrides = {}) => ({ keywords: [], filter: '', condition: 'all', timeframe: '', ...overrides });

function generate({
  metadata = {}, logSource = {}, conditions = [], detection = {}, fields = [], references = [], tags = [], falsePositives = [],
} = {}) {
  return generateSigmaRule(
    _metadata(metadata), { ...emptyLogSource, ...logSource }, conditions, detections(detection),
    fields, references, tags, falsePositives,
  );
}

const parse = (opts) => yaml.load(generate(opts));

describe('generateSigmaRule', () => {
  it('throws when a required metadata field is missing', () => {
    expect(() => generate({ metadata: { title: '' } })).toThrow('title is required');
  });

  it('emits spec fields with lower-case status/level', () => {
    expect(parse()).toEqual({
      title: 'Suspicious PowerShell',
      id: 'abc-123',
      status: 'experimental',
      level: 'high',
      logsource: null,
      detection: null,
    });
  });

  it('omits the "None" placeholders and empty optional fields', () => {
    const rule = generate({ metadata: { status: 'None', level: 'None' } });
    expect(rule).not.toMatch(/status:|level:|description:|date:|author:/);
  });

  it('joins authors into the single `author` field', () => {
    expect(parse({ metadata: { authors: [item('Alice'), item('Bob')] } }).author).toBe('Alice, Bob');
  });

  it('quotes values that would otherwise break the YAML', () => {
    const doc = parse({
      metadata: { title: 'Mimikatz: sekurlsa #1', description: "it's \"quoted\"", license: 'DRL-1.1' },
      references: [item('https://example.com/a?b=1#frag')],
      falsePositives: [item('yes')],
    });
    expect(doc.title).toBe('Mimikatz: sekurlsa #1');
    expect(doc.description).toBe("it's \"quoted\"");
    expect(doc.references).toEqual(['https://example.com/a?b=1#frag']);
    expect(doc.falsepositives).toEqual(['yes']); // not coerced to a boolean
    expect(doc.license).toBe('DRL-1.1');
  });

  it('renders the populated logsource fields', () => {
    expect(parse({ logSource: { product: 'windows', category: 'process_creation' } }).logsource).toEqual({
      product: 'windows', category: 'process_creation',
    });
  });

  it('renders selection conditions as a field|modifier mapping', () => {
    // Regression: these came out as `CommandLine equals "x"` / `CommandLine|contains contains "x"`.
    const doc = parse({
      conditions: [
        cond('Image', 'endswith', '\\vssadmin.exe'),
        cond('CommandLine', 'contains', 'delete shadows'),
        cond('CommandLine', 'contains', 'resize shadowstorage'),
        cond('User', 'equals', 'NT AUTHORITY\\SYSTEM'),
      ],
    });
    expect(doc.detection).toEqual({
      selection: {
        'Image|endswith': '\\vssadmin.exe',
        'CommandLine|contains': ['delete shadows', 'resize shadowstorage'],
        User: 'NT AUTHORITY\\SYSTEM',
      },
      condition: 'selection',
    });
  });

  it('includes keywords and combines identifiers per the chosen condition', () => {
    // Regression: keywords lived in component state and never reached the rule.
    const conditions = [cond('Image', 'equals', 'a.exe')];
    const keywords = [item('mimikatz'), item('sekurlsa::logonpasswords')];
    expect(parse({ conditions, detection: { keywords } }).detection).toEqual({
      selection: { Image: 'a.exe' },
      keywords: ['mimikatz', 'sekurlsa::logonpasswords'],
      condition: 'selection and keywords',
    });
    expect(parse({ conditions, detection: { keywords, condition: 'any' } }).detection.condition).toBe('selection or keywords');
    expect(parse({ conditions, detection: { condition: '1 of them' } }).detection.condition).toBe('1 of them');
  });

  it('a custom condition expression overrides the dropdown; timeframe is kept', () => {
    const doc = parse({
      conditions: [cond('Image', 'equals', 'a.exe')],
      detection: { filter: 'selection | count() > 5', timeframe: '24h' },
    });
    expect(doc.detection.condition).toBe('selection | count() > 5');
    expect(doc.detection.timeframe).toBe('24h');
  });

  it('lists tags, references, falsepositives and fields', () => {
    const doc = parse({
      tags: [item('attack.execution')],
      references: [item('https://example.com')],
      falsePositives: [item('Admin scripts')],
      fields: [item('CommandLine')],
    });
    expect(doc.tags).toEqual(['attack.execution']);
    expect(doc.references).toEqual(['https://example.com']);
    expect(doc.falsepositives).toEqual(['Admin scripts']);
    expect(doc.fields).toEqual(['CommandLine']);
  });
});

describe('yamlScalar / buildSigmaCondition', () => {
  it.each([
    ['plain_word', 'plain_word'],
    ['two words', 'two words'],
    ['a: b', "'a: b'"],
    ["o'brien", "'o''brien'"],
    ['-leading', "'-leading'"],
    ['null', "'null'"],
    ['', "''"],
  ])('%j -> %s', (input, out) => {
    expect(yamlScalar(input)).toBe(out);
  });

  it('no identifiers and no custom expression means no condition', () => {
    expect(buildSigmaCondition(detections(), [])).toBe(null);
  });
});

describe('createInitialMetadata', () => {
  it('generates a fresh UUID and today\'s date, with idle defaults for the rest', () => {
    const metadata = createInitialMetadata();

    expect(metadata.id).toMatch(/^[0-9a-f-]{36}$/i);
    expect(metadata.date).toBe(new Date().toISOString().split('T')[0]);
    expect(metadata.title).toBe('');
    expect(metadata.level).toBe('None');
    expect(metadata.status).toBe('None');
  });
});

describe('createInitialLogSource', () => {
  it('returns all-empty fields', () => {
    expect(createInitialLogSource()).toEqual(emptyLogSource);
  });
});

describe('createInitialDetection', () => {
  it('defaults condition to "all" with no keywords/filter/timeframe', () => {
    expect(createInitialDetection()).toEqual({ keywords: [], filter: '', condition: 'all', timeframe: '' });
  });
});

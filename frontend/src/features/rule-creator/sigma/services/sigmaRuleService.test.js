import {
  generateSigmaRule,
  createInitialMetadata,
  createInitialLogSource,
  createInitialDetection,
} from './sigmaRuleService';

function _metadata(overrides = {}) {
  return {
    title: 'Suspicious PowerShell',
    id: 'abc-123',
    status: 'experimental',
    description: '',
    authors: [],
    date: '',
    modified: '',
    license: '',
    level: 'high',
    ...overrides,
  };
}

const emptyLogSource = { product: '', category: '', service: '', definition: '' };
const emptyDetections = { filter: '', condition: '', timeframe: '' };

describe('generateSigmaRule', () => {
  it('throws when a required metadata field is missing', () => {
    expect(() =>
      generateSigmaRule(_metadata({ title: '' }), emptyLogSource, [], emptyDetections, [], [], [], []),
    ).toThrow('title is required');
  });

  it('renders the required fields plus level for a minimal rule', () => {
    const rule = generateSigmaRule(
      _metadata(),
      emptyLogSource,
      [],
      emptyDetections,
      [],
      [],
      [],
      [],
    );

    expect(rule).toContain('title: Suspicious PowerShell\n');
    expect(rule).toContain('id: abc-123\n');
    expect(rule).toContain('status: experimental\n');
    expect(rule).toContain('level: high\n');
    expect(rule).toContain('detection:\n');
  });

  it('omits optional metadata fields that are empty', () => {
    const rule = generateSigmaRule(
      _metadata(),
      emptyLogSource,
      [],
      emptyDetections,
      [],
      [],
      [],
      [],
    );

    expect(rule).not.toContain('description:');
    expect(rule).not.toContain('date:');
    expect(rule).not.toContain('authors:');
  });

  it('lists authors under an authors: block', () => {
    const rule = generateSigmaRule(
      _metadata({ authors: [{ value: 'Alice' }, { value: 'Bob' }] }),
      emptyLogSource,
      [],
      emptyDetections,
      [],
      [],
      [],
      [],
    );

    expect(rule).toContain('authors:\n  - Alice\n  - Bob\n');
  });

  it('renders the logsource block only for populated fields', () => {
    const rule = generateSigmaRule(
      _metadata(),
      { product: 'windows', category: 'process_creation', service: '', definition: '' },
      [],
      emptyDetections,
      [],
      [],
      [],
      [],
    );

    expect(rule).toContain('logsource:\n  product: windows\n  category: process_creation\n');
    expect(rule).not.toContain('service:');
  });

  it('renders selection conditions with the equals modifier bare', () => {
    const rule = generateSigmaRule(
      _metadata(),
      emptyLogSource,
      [{ field: 'CommandLine', modifier: 'equals', value: 'evil.exe' }],
      emptyDetections,
      [],
      [],
      [],
      [],
    );

    expect(rule).toContain('  selection:\n    CommandLine equals "evil.exe"\n');
  });

  it('renders a non-equals modifier with the |modifier suffix', () => {
    const rule = generateSigmaRule(
      _metadata(),
      emptyLogSource,
      [{ field: 'CommandLine', modifier: 'contains', value: 'evil' }],
      emptyDetections,
      [],
      [],
      [],
      [],
    );

    expect(rule).toContain('CommandLine|contains contains "evil"');
  });

  it('includes filter/condition/timeframe when present', () => {
    const rule = generateSigmaRule(
      _metadata(),
      emptyLogSource,
      [],
      { filter: 'not test', condition: 'selection and not filter', timeframe: '24h' },
      [],
      [],
      [],
      [],
    );

    expect(rule).toContain('  filter:\n    not test\n');
    expect(rule).toContain('  condition: selection and not filter\n');
    expect(rule).toContain('  timeframe: 24h\n');
  });

  it('lists tags, references, falsepositives, and fields in their own blocks', () => {
    const rule = generateSigmaRule(
      _metadata(),
      emptyLogSource,
      [],
      emptyDetections,
      [{ value: 'CommandLine' }],
      [{ value: 'https://example.com' }],
      [{ value: 'attack.execution' }],
      [{ value: 'Admin scripts' }],
    );

    expect(rule).toContain('tags:\n  - attack.execution\n');
    expect(rule).toContain('references:\n  - https://example.com\n');
    expect(rule).toContain('falsepositives:\n  - Admin scripts\n');
    expect(rule).toContain('fields:\n  - CommandLine\n');
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
    expect(createInitialLogSource()).toEqual({
      product: '',
      category: '',
      service: '',
      definition: '',
    });
  });
});

describe('createInitialDetection', () => {
  it('defaults condition to "all" with empty selection/filter/timeframe', () => {
    expect(createInitialDetection()).toEqual({
      selection: [],
      filter: '',
      condition: 'all',
      timeframe: '',
    });
  });
});

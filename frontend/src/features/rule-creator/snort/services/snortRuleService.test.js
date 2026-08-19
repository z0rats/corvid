import { generateSnortRule, buildMetadata, createInitialRuleHeader, createInitialRuleOptions, createInitialRuleContent, createInitialRuleMetadata } from './snortRuleService';

const header = {
  action: 'alert',
  protocol: 'tcp',
  sourceIP: 'any',
  sourcePort: 'any',
  direction: '->',
  destIP: '$HOME_NET',
  destPort: '80',
};

function options(overrides = {}) {
  return {
    msg: 'Suspicious HTTP request',
    sid: '1000001',
    rev: '1',
    classtype: '',
    priority: '',
    reference: [],
    metadata: [],
    ...overrides,
  };
}

const emptyContent = { content: [], pcre: [], flowbits: [], threshold: '', detection_filter: '' };
const emptyMetadata = {};

describe('generateSnortRule', () => {
  it('throws when a required option is missing', () => {
    expect(() =>
      generateSnortRule(header, options({ msg: '' }), emptyContent, emptyMetadata),
    ).toThrow('msg is required');
  });

  it('renders the header and required options for a minimal rule', () => {
    const rule = generateSnortRule(header, options(), emptyContent, emptyMetadata);

    expect(rule).toBe(
      'alert tcp any any -> $HOME_NET 80 (msg:"Suspicious HTTP request"; sid:1000001; rev:1)',
    );
  });

  it('includes classtype and priority only when set', () => {
    const rule = generateSnortRule(
      header,
      options({ classtype: 'trojan-activity', priority: '1' }),
      emptyContent,
      emptyMetadata,
    );

    expect(rule).toContain('classtype:trojan-activity');
    expect(rule).toContain('priority:1');
  });

  it('renders content matches with their modifiers', () => {
    const rule = generateSnortRule(
      header,
      options(),
      {
        ...emptyContent,
        content: [{ value: 'evil', modifiers: ['nocase', 'http_uri'] }],
      },
      emptyMetadata,
    );

    expect(rule).toContain('content:"evil"; nocase; http_uri');
  });

  it('renders pcre and flowbits entries', () => {
    const rule = generateSnortRule(
      header,
      options(),
      {
        ...emptyContent,
        pcre: [{ pattern: '/foo.*bar/i' }],
        flowbits: [{ action: 'set', name: 'malware.detected' }],
      },
      emptyMetadata,
    );

    expect(rule).toContain('pcre:"/foo.*bar/i"');
    expect(rule).toContain('flowbits:set,malware.detected');
  });

  it('renders threshold and detection_filter when present', () => {
    const rule = generateSnortRule(
      header,
      options(),
      { ...emptyContent, threshold: 'type limit, track by_src, count 5, seconds 60', detection_filter: '' },
      emptyMetadata,
    );

    expect(rule).toContain('threshold:type limit, track by_src, count 5, seconds 60');
  });

  it('renders each reference as type,value', () => {
    const rule = generateSnortRule(
      header,
      options({ reference: [{ type: 'cve', value: '2024-1234' }] }),
      emptyContent,
      emptyMetadata,
    );

    expect(rule).toContain('reference:cve,2024-1234');
  });

  it('joins basic and enhanced metadata into one metadata: option', () => {
    const rule = generateSnortRule(
      header,
      options({ metadata: [{ key: 'author', value: 'analyst' }] }),
      emptyContent,
      { policy: 'balanced-ips', created_at: '2024_01_01' },
    );

    expect(rule).toContain('metadata:author analyst, created_at 2024_01_01, policy balanced-ips');
  });

  it('omits the metadata option entirely when there is none', () => {
    const rule = generateSnortRule(header, options(), emptyContent, emptyMetadata);

    expect(rule).not.toContain('metadata:');
  });
});

describe('buildMetadata', () => {
  it('combines basic key/value pairs with enhanced metadata fields', () => {
    const metadata = buildMetadata(
      [{ key: 'author', value: 'analyst' }],
      {
        created_at: '2024_01_01',
        updated_at: '2024_02_01',
        policy: 'security-ips',
        former_category: 'MALWARE',
        signature_severity: 'Major',
        attack_target: ['Client_Endpoint'],
        deployment: ['Perimeter'],
        tag: [{ value: 'ransomware' }],
        malware_family: [{ value: 'Emotet' }],
      },
    );

    expect(metadata).toEqual([
      'author analyst',
      'created_at 2024_01_01',
      'updated_at 2024_02_01',
      'policy security-ips',
      'former_category MALWARE',
      'signature_severity Major',
      'attack_target Client_Endpoint',
      'deployment Perimeter',
      'tag ransomware',
      'malware_family Emotet',
    ]);
  });

  it('returns an empty array when nothing is set', () => {
    expect(buildMetadata([], {})).toEqual([]);
  });

  it('tolerates enhanced metadata missing the array fields entirely', () => {
    expect(buildMetadata([], { policy: 'balanced-ips' })).toEqual(['policy balanced-ips']);
  });
});

describe('createInitialRuleHeader', () => {
  it('defaults to a generic any-to-any TCP alert', () => {
    expect(createInitialRuleHeader()).toEqual({
      action: 'alert',
      protocol: 'tcp',
      sourceIP: 'any',
      sourcePort: 'any',
      direction: '->',
      destIP: 'any',
      destPort: 'any',
    });
  });
});

describe('createInitialRuleOptions', () => {
  it('generates a 6-digit SID string and rev 1', () => {
    const opts = createInitialRuleOptions();
    expect(opts.sid).toMatch(/^\d{6}$/);
    expect(opts.rev).toBe('1');
    expect(opts.priority).toBe('3');
  });
});

describe('createInitialRuleContent', () => {
  it('returns empty arrays for every content mechanism', () => {
    expect(createInitialRuleContent()).toEqual({
      content: [],
      pcre: [],
      flowbits: [],
      threshold: '',
      detection_filter: '',
    });
  });
});

describe('createInitialRuleMetadata', () => {
  it("sets created_at and updated_at to today's date", () => {
    const metadata = createInitialRuleMetadata();
    const today = new Date().toISOString().split('T')[0];
    expect(metadata.created_at).toBe(today);
    expect(metadata.updated_at).toBe(today);
  });
});

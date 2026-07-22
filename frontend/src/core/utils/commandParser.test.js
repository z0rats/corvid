import {
  parseQuery,
  matchTools,
  rankToolsForValue,
  resolvePlaybook,
  getWhichKeySuggestions,
  TYPE_TOKEN_ALIASES,
  BUILTIN_ACTIONS,
} from './commandParser';
import { IOC_TYPES } from './iocTypeDetection';

const registry = [
  {
    id: 'reddit_search', label: 'Reddit Search', path: '/reddit-search',
    aliases: ['reddit', 'reddit search', 'rosint'], tags: ['identity', 'recon'], accepts: [], acceptsRouting: {},
  },
  {
    id: 'username_search', label: 'Username Search', path: '/username-search',
    aliases: ['username search', 'maigret', 'sherlock'], tags: ['identity', 'recon'], accepts: [], acceptsRouting: {},
  },
  {
    id: 'ioc_tools', label: 'IOC Tools', path: '/ioc-tools',
    aliases: ['ioc', 'lookup', 'whois'], tags: ['ioc', 'recon'],
    accepts: [IOC_TYPES.IPV4, IOC_TYPES.IPV6, IOC_TYPES.DOMAIN, IOC_TYPES.EMAIL, IOC_TYPES.MD5, IOC_TYPES.SHA1, IOC_TYPES.SHA256],
    acceptsRouting: { [IOC_TYPES.MD5]: '/ioc-tools/bulk' },
  },
  {
    id: 'dork_runner', label: 'Dork Runner', path: '/dork-runner',
    aliases: ['dork runner', 'dork'], tags: ['recon'], accepts: [IOC_TYPES.DOMAIN], acceptsRouting: {},
  },
];

const playbooks = [
  { name: 'identity-triage', steps: ['username_search', 'reddit_search'], createdAt: 1 },
];

describe('parseQuery — empty input', () => {
  it('returns kind "empty" for blank/whitespace-only input', () => {
    expect(parseQuery('', { registry })).toEqual({ kind: 'empty' });
    expect(parseQuery('   ', { registry })).toEqual({ kind: 'empty' });
    expect(parseQuery(undefined, { registry })).toEqual({ kind: 'empty' });
  });
});

describe('parseQuery — plain text fuzzy match', () => {
  it('matches by tool alias', () => {
    const result = parseQuery('reddit', { registry });
    expect(result.kind).toBe('text');
    expect(result.matches[0].id).toBe('reddit_search');
  });

  it('matches by alias substring', () => {
    const result = parseQuery('maigret', { registry });
    expect(result.matches[0].id).toBe('username_search');
  });

  it('falls back to identity-tool suggestions for a query that matches no tool by name', () => {
    // Superseded plain "no matches" now that the registry has identity-tagged tools to fall
    // back to — see the dedicated "identity-tool fallback" describe block below.
    const result = parseQuery('zzz-nonexistent-tool', { registry });
    expect(result.kind).toBe('fallback');
  });
});

describe('parseQuery — recognized value', () => {
  it('detects an IP and ranks tools that accept it', () => {
    const result = parseQuery('185.220.101.7', { registry });
    expect(result.kind).toBe('value');
    expect(result.iocType).toBe(IOC_TYPES.IPV4);
    expect(result.matches.map((m) => m.id)).toEqual(['ioc_tools']);
  });

  it('detects a CVE id', () => {
    const result = parseQuery('CVE-2024-3400', { registry });
    expect(result.kind).toBe('value');
    expect(result.iocType).toBe(IOC_TYPES.CVE);
  });

  it('ranks multiple tools for a domain (ioc_tools and dork_runner both accept it)', () => {
    const result = parseQuery('evil.com', { registry });
    expect(result.kind).toBe('value');
    expect(result.matches.map((m) => m.id).sort()).toEqual(['dork_runner', 'ioc_tools']);
  });
});

describe('parseQuery — #tag filter', () => {
  it('filters the registry by tag', () => {
    const result = parseQuery('#identity', { registry });
    expect(result.kind).toBe('tag');
    expect(result.matches.map((m) => m.id).sort()).toEqual(['reddit_search', 'username_search']);
  });

  it('is case-insensitive on the tag name', () => {
    const result = parseQuery('#RECON', { registry });
    expect(result.matches.length).toBeGreaterThan(0);
  });

  it('returns which-key suggestions for a bare "#"', () => {
    const result = parseQuery('#', { registry });
    expect(result.kind).toBe('which-key');
    expect(result.operator).toBe('#');
    expect(result.suggestions).toEqual(['identity', 'ioc', 'recon']);
  });
});

describe('parseQuery — type:kind filter', () => {
  it('filters by a single ioc type token', () => {
    const result = parseQuery('type:email', { registry });
    expect(result.kind).toBe('type');
    expect(result.matches.map((m) => m.id)).toEqual(['ioc_tools']);
  });

  it('"hash" resolves to md5/sha1/sha256 collectively', () => {
    const result = parseQuery('type:hash', { registry });
    expect(result.iocTypes).toEqual([IOC_TYPES.MD5, IOC_TYPES.SHA1, IOC_TYPES.SHA256]);
    expect(result.matches.map((m) => m.id)).toEqual(['ioc_tools']);
  });

  it('an unknown type token yields no matches, not an error', () => {
    const result = parseQuery('type:not-a-real-type', { registry });
    expect(result.kind).toBe('type');
    expect(result.matches).toEqual([]);
  });

  it('returns which-key suggestions for a bare "type:"', () => {
    const result = parseQuery('type:', { registry });
    expect(result.kind).toBe('which-key');
    expect(result.operator).toBe('type:');
    expect(result.suggestions).toEqual(Object.keys(TYPE_TOKEN_ALIASES).sort());
  });
});

describe('parseQuery — >action', () => {
  it('parses >settings and >theme', () => {
    expect(parseQuery('>settings', { registry })).toEqual({ kind: 'action', action: 'settings' });
    expect(parseQuery('>theme', { registry })).toEqual({ kind: 'action', action: 'theme' });
  });

  it('parses >record', () => {
    expect(parseQuery('>record', { registry })).toEqual({ kind: 'action', action: 'record-start' });
  });

  it('parses bare >record:stop with no name', () => {
    const result = parseQuery('>record:stop', { registry });
    expect(result).toEqual({ kind: 'action', action: 'record-stop', name: null });
  });

  it('parses >record:stop with a trailing name', () => {
    const result = parseQuery('>record:stop identity-triage', { registry });
    expect(result).toEqual({ kind: 'action', action: 'record-stop', name: 'identity-triage' });
  });

  it('parses >playbook:manage', () => {
    expect(parseQuery('>playbook:manage', { registry })).toEqual({ kind: 'action', action: 'playbook-manage' });
  });

  it('parses >playbook:name value', () => {
    const result = parseQuery('>playbook:identity-triage john_doe', { registry });
    expect(result).toEqual({
      kind: 'action', action: 'playbook-run', playbookName: 'identity-triage', value: 'john_doe',
    });
  });

  it('parses >playbook:name with no trailing value', () => {
    const result = parseQuery('>playbook:identity-triage', { registry });
    expect(result).toEqual({
      kind: 'action', action: 'playbook-run', playbookName: 'identity-triage', value: null,
    });
  });

  it('an unrecognized >action falls back to kind "unknown"', () => {
    const result = parseQuery('>not-a-real-action', { registry });
    expect(result).toEqual({ kind: 'action', action: 'unknown', raw: 'not-a-real-action' });
  });

  it('returns which-key suggestions for a bare ">"', () => {
    const result = parseQuery('>', { registry, playbooks });
    expect(result.kind).toBe('which-key');
    expect(result.operator).toBe('>');
    expect(result.suggestions).toEqual([...BUILTIN_ACTIONS, 'playbook:identity-triage']);
  });

  it('">" which-key includes "record:stop" only while recording', () => {
    const result = parseQuery('>', { registry, playbooks: [], isRecording: true });
    expect(result.suggestions).toContain('record:stop');
  });

  it('lists playbook names for a bare ">playbook:"', () => {
    const result = parseQuery('>playbook:', { registry, playbooks });
    expect(result.kind).toBe('which-key');
    expect(result.suggestions).toEqual(['playbook:identity-triage']);
  });
});

describe('parseQuery — value+tool pivot', () => {
  it('splits the trailing token as the tool and the rest as the value ("value tool")', () => {
    const result = parseQuery('john_doe reddit', { registry });
    expect(result.kind).toBe('pivot');
    expect(result.value).toBe('john_doe');
    expect(result.tool.id).toBe('reddit_search');
  });

  it('splits the leading token as the tool and the rest as the value ("tool value")', () => {
    const result = parseQuery('reddit john_doe', { registry });
    expect(result.kind).toBe('pivot');
    expect(result.value).toBe('john_doe');
    expect(result.tool.id).toBe('reddit_search');
  });

  it('prefers the "value tool" reading when both ends happen to match a tool', () => {
    // Both "maigret" (username_search) and "reddit" (reddit_search) are real tool aliases here —
    // the trailing-token reading wins, same as before bidirectional support existed.
    const result = parseQuery('maigret reddit', { registry });
    expect(result.value).toBe('maigret');
    expect(result.tool.id).toBe('reddit_search');
  });

  it('falls back to the identity-tool suggestion list when neither end matches a tool', () => {
    // Was plain "no matches" text before the Alfred/Raycast-style fallback existed.
    const result = parseQuery('john_doe nonexistenttool', { registry });
    expect(result.kind).toBe('fallback');
    expect(result.value).toBe('john_doe nonexistenttool');
  });

  it('a recognized value takes priority over the pivot interpretation', () => {
    // "185.220.101.7" alone is a full IP, not "185.220.101 .7 <tool>" — sanity check that a
    // bare recognized value never gets pivot-parsed.
    const result = parseQuery('185.220.101.7', { registry });
    expect(result.kind).toBe('value');
  });
});

describe('parseQuery — identity-tool fallback for an unrecognized bare value', () => {
  const registryWithEmail = [
    ...registry,
    {
      id: 'email_search', label: 'Email Search', path: '/email-search',
      aliases: ['email search', 'mailcat'], tags: ['email', 'identity'], accepts: [], acceptsRouting: {},
    },
  ];

  it('suggests every identity-tagged tool for a bare, unrecognized value', () => {
    const result = parseQuery('z0rats', { registry: registryWithEmail });
    expect(result.kind).toBe('fallback');
    expect(result.value).toBe('z0rats');
    expect(result.matches.map((m) => m.id).sort()).toEqual(['email_search', 'reddit_search', 'username_search']);
  });

  it('promotes email-tagged tools to the front when the value looks email-shaped', () => {
    const result = parseQuery('z0rats@', { registry: registryWithEmail });
    expect(result.kind).toBe('fallback');
    expect(result.matches[0].id).toBe('email_search');
  });

  it('falls back to plain "no matches" text when the registry has no identity-tagged tools', () => {
    const noIdentityRegistry = registry.filter((e) => !e.tags.includes('identity'));
    const result = parseQuery('z0rats', { registry: noIdentityRegistry });
    expect(result).toEqual({ kind: 'text', query: 'z0rats', matches: [] });
  });
});

describe('parseQuery — defang/fang instant answer', () => {
  it('parses "defang <value>"', () => {
    const result = parseQuery('defang 185.220.101.7', { registry });
    expect(result).toEqual({ kind: 'instant', op: 'defang', value: '185.220.101.7' });
  });

  it('parses "fang <value>"', () => {
    const result = parseQuery('fang hxxp://evil[.]com', { registry });
    expect(result).toEqual({ kind: 'instant', op: 'fang', value: 'hxxp://evil[.]com' });
  });

  it('is case-insensitive on the command word', () => {
    const result = parseQuery('DEFANG 185.220.101.7', { registry });
    expect(result.kind).toBe('instant');
    expect(result.op).toBe('defang');
  });

  it('"defang" with no value is not treated as an instant answer', () => {
    const result = parseQuery('defang', { registry });
    expect(result.kind).not.toBe('instant');
  });
});

describe('matchTools', () => {
  it('ranks exact match above prefix and substring matches', () => {
    const results = matchTools('dork', registry);
    expect(results[0].id).toBe('dork_runner');
  });

  it('returns an empty array for no query', () => {
    expect(matchTools('', registry)).toEqual([]);
  });
});

describe('rankToolsForValue', () => {
  it('returns only entries whose accepts includes the type', () => {
    expect(rankToolsForValue(IOC_TYPES.SHA1, registry).map((e) => e.id)).toEqual(['ioc_tools']);
  });

  it('returns an empty array when nothing accepts the type', () => {
    expect(rankToolsForValue(IOC_TYPES.CVE, registry)).toEqual([]);
  });
});

describe('resolvePlaybook', () => {
  it('finds a playbook by name', () => {
    expect(resolvePlaybook('identity-triage', playbooks)?.steps).toEqual(['username_search', 'reddit_search']);
  });

  it('returns null when not found', () => {
    expect(resolvePlaybook('nope', playbooks)).toBeNull();
  });
});

describe('getWhichKeySuggestions', () => {
  it('returns every unique tag, sorted, for "#"', () => {
    expect(getWhichKeySuggestions('#', { registry })).toEqual(['identity', 'ioc', 'recon']);
  });

  it('returns every type token, sorted, for "type:"', () => {
    expect(getWhichKeySuggestions('type:', { registry })).toEqual(Object.keys(TYPE_TOKEN_ALIASES).sort());
  });

  it('returns builtin actions plus playbook names for ">"', () => {
    expect(getWhichKeySuggestions('>', { registry, playbooks })).toEqual([
      ...BUILTIN_ACTIONS,
      'playbook:identity-triage',
    ]);
  });

  it('includes "record:stop" only while recording', () => {
    const notRecording = getWhichKeySuggestions('>', { registry, playbooks: [], isRecording: false });
    const recording = getWhichKeySuggestions('>', { registry, playbooks: [], isRecording: true });
    expect(notRecording).not.toContain('record:stop');
    expect(recording).toContain('record:stop');
  });

  it('returns an empty array for an unrecognized operator', () => {
    expect(getWhichKeySuggestions('$', { registry })).toEqual([]);
  });
});

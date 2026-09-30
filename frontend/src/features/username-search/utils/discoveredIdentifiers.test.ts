import { aggregateDiscovered, guessEmails } from './discoveredIdentifiers';

describe('aggregateDiscovered', () => {
  const sites = [
    {
      site_name: 'GitHub',
      extra: {
        discovered_usernames: [{ value: 'JSmith_alt', type: 'username' }, { value: 'jsmith', type: 'username' }],
        discovered_names: ['John Smith'],
      },
    },
    {
      site_name: 'Reddit',
      extra: { discovered_usernames: [{ value: 'jsmith_alt', type: 'username' }], discovered_names: ['john smith'] },
    },
    { site_name: 'Plain', extra: null },
  ];

  it('dedupes case-insensitively, tracks source sites, and excludes the searched handle', () => {
    const { usernames, names } = aggregateDiscovered(sites, 'JSmith');
    expect(usernames).toEqual([{ value: 'JSmith_alt', type: 'username', sites: ['GitHub', 'Reddit'] }]);
    expect(names).toEqual([{ value: 'John Smith', sites: ['GitHub', 'Reddit'] }]);
  });

  it('tolerates missing input', () => {
    expect(aggregateDiscovered(null, 'x')).toEqual({ usernames: [], names: [] });
  });
});

describe('guessEmails', () => {
  it('builds candidates per provider', () => {
    expect(guessEmails('John.Smith', ['gmail.com'])).toEqual(['john.smith@gmail.com']);
  });

  it('rejects handles that cannot be an email local part', () => {
    expect(guessEmails('john smith')).toEqual([]);
    expect(guessEmails('a..b')).toEqual([]);
    expect(guessEmails('john.')).toEqual([]);
    expect(guessEmails('')).toEqual([]);
  });
});

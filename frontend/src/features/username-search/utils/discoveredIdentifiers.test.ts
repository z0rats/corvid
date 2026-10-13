import { guessEmails } from './discoveredIdentifiers';

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

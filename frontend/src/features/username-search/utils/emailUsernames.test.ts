import { emailUsernameCandidates, parseEmail } from './emailUsernames';

const values = (email: string) => emailUsernameCandidates(email).map((c) => c.value);

describe('parseEmail', () => {
  it('splits a bare address and lowercases the domain', () => {
    expect(parseEmail(' J.Doe@GMail.com ')).toEqual({ local: 'J.Doe', domain: 'gmail.com' });
  });

  it('rejects non-emails', () => {
    expect(parseEmail('johndoe')).toBeNull();
    expect(parseEmail('john@localhost')).toBeNull();
    expect(parseEmail('a b@example.com')).toBeNull();
  });
});

describe('emailUsernameCandidates', () => {
  it('Gmail: drops the +tag and adds the dotless form, exact first', () => {
    expect(emailUsernameCandidates('J.Doe+x@gmail.com')).toEqual([
      { value: 'j.doe', reason: 'untagged' },
      { value: 'jdoe', reason: 'gmailDots' },
      { value: 'j_doe', reason: 'separator' },
      { value: 'j-doe', reason: 'separator' },
    ]);
  });

  it('treats googlemail.com like gmail.com', () => {
    expect(emailUsernameCandidates('a.b.c@googlemail.com').map((c) => c.reason)).toContain('gmailDots');
  });

  it('keeps dots for non-Gmail providers: no gmailDots candidate', () => {
    const candidates = emailUsernameCandidates('j.doe@outlook.com');
    expect(candidates[0]).toEqual({ value: 'j.doe', reason: 'exact' });
    expect(candidates.some((c) => c.reason === 'gmailDots')).toBe(false);
    // `jdoe` still appears, but only as a separator guess.
    expect(candidates.find((c) => c.value === 'jdoe')?.reason).toBe('separator');
  });

  it('strips +tag for any provider', () => {
    expect(values('johndoe+news@fastmail.com')).toEqual(['johndoe']);
  });

  it('varies separators of a first_last local part', () => {
    expect(values('john_smith@proton.me')).toEqual(['john_smith', 'johnsmith', 'john-smith', 'john.smith']);
  });

  it('drops candidates that are too short or not valid usernames', () => {
    expect(values('jd@gmail.com')).toEqual([]);
    expect(values("o'neil@example.com")).toEqual([]);
  });

  it('never returns a candidate containing +', () => {
    expect(values('a.b+c+d@gmail.com').some((v) => v.includes('+'))).toBe(false);
  });

  it('dedupes', () => {
    const out = values('johndoe@gmail.com');
    expect(out).toEqual(['johndoe']);
  });

  it('returns nothing for a non-email', () => {
    expect(emailUsernameCandidates('johndoe')).toEqual([]);
  });
});

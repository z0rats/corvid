import { describe, it, expect } from 'vitest';
import { refang } from './refang';

describe('refang', () => {
  it.each([
    ['185.220.101[.]7', '185.220.101.7'],
    ['185(.)220(.)101(.)7', '185.220.101.7'],
    ['evil[dot]com', 'evil.com'],
    ['hxxps[://]evil[.]com/path', 'https://evil.com/path'],
    ['hXXp://evil{.}com', 'http://evil.com'],
    ['hxxps[:]//evil[.]com', 'https://evil.com'],
    ['fxp[://]files[.]example[.]org', 'ftp://files.example.org'],
    ['user[@]example[.]com', 'user@example.com'],
    ['user[at]example(.)com', 'user@example.com'],
    ['  1.2.3.4  ', '1.2.3.4'],
  ])('%s -> %s', (input, expected) => {
    expect(refang(input)).toBe(expected);
  });

  it('leaves already-fanged and non-IOC values untouched', () => {
    expect(refang('https://example.com/a?b=c')).toBe('https://example.com/a?b=c');
    expect(refang('d41d8cd98f00b204e9800998ecf8427e')).toBe('d41d8cd98f00b204e9800998ecf8427e');
    expect(refang('CVE-2024-3094')).toBe('CVE-2024-3094');
  });

  it('only rewrites hxxp as a leading scheme', () => {
    expect(refang('example.com/hxxp:')).toBe('example.com/hxxp:');
  });
});

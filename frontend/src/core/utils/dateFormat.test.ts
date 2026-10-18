import { describe, expect, it } from 'vitest';
import { formatDateTime, formatRelativeTime } from './dateFormat';

const NOW = new Date('2026-10-18T12:00:00Z');
const ago = (seconds: number) => new Date(NOW.getTime() - seconds * 1000);

describe('formatRelativeTime', () => {
  it.each([
    [10, 'now'],
    [90, '2 minutes ago'],
    [3 * 3600, '3 hours ago'],
    [24 * 3600, 'yesterday'],
    [3 * 24 * 3600, '3 days ago'],
    [14 * 24 * 3600, '2 weeks ago'],
    [400 * 24 * 3600, 'last year'],
  ])('%i seconds ago -> %s', (seconds, expected) => {
    expect(formatRelativeTime(ago(seconds), NOW)).toBe(expected);
  });

  it('formats future dates', () => {
    expect(formatRelativeTime(ago(-2 * 3600), NOW)).toBe('in 2 hours');
  });
});

describe('formatDateTime', () => {
  it('renders a long date and a 12-hour time', () => {
    const date = new Date(2026, 9, 18, 15, 4);
    expect(formatDateTime(date)).toBe('October 18, 2026, 3:04 PM');
  });
});

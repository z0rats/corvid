import { formatCompact, formatDate, formatPercent } from './telegramFormat';
import { estimateRequests, indicatorPivotPath } from './telegramSearchConfig';

describe('telegramFormat', () => {
  it('formats compact counts', () => {
    expect(formatCompact(10287298)).toBe('10.3M');
    expect(formatCompact(83253)).toBe('83.3K');
    expect(formatCompact(239)).toBe('239');
    expect(formatCompact(0)).toBe('0');
    expect(formatCompact(null)).toBeNull();
  });

  it('formats ratios as whole percents', () => {
    expect(formatPercent(0.2534)).toBe('25%');
    expect(formatPercent(0)).toBe('0%');
    expect(formatPercent(undefined)).toBeNull();
  });

  it('formats dates, null when absent', () => {
    expect(formatDate('2015-10-28T18:20:58+00:00')).toBeTruthy();
    expect(formatDate(null)).toBeNull();
  });
});

describe('telegramSearchConfig', () => {
  it('estimates requests: card + pages + creation lookup', () => {
    expect(estimateRequests(100)).toBe(7);
    expect(estimateRequests(500)).toBe(27);
  });

  it.each([
    ['domains', '/ioc-tools/domain-finder'],
    ['md5', '/ioc-tools/bulk'],
    ['sha256', '/ioc-tools/bulk'],
    ['urls', '/ioc-tools/lookup'],
    ['ips', '/ioc-tools/lookup'],
    ['emails', '/ioc-tools/lookup'],
    ['cves', '/ioc-tools/lookup'],
  ])('routes %s indicators to %s', (type, path) => {
    expect(indicatorPivotPath(type)).toBe(path);
  });
});

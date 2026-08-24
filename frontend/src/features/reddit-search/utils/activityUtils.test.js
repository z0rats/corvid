import { buildHourlyActivity, buildMonthlyActivity } from './activityUtils';

function itemAt(isoString) {
  return { created_utc: Math.floor(new Date(isoString).getTime() / 1000) };
}

describe('buildHourlyActivity', () => {
  it('returns 24 zero-count buckets for an empty/missing list', () => {
    expect(buildHourlyActivity([])).toHaveLength(24);
    expect(buildHourlyActivity([]).every((b) => b.count === 0)).toBe(true);
    expect(buildHourlyActivity(undefined)).toHaveLength(24);
  });

  it('buckets items by local hour-of-day', () => {
    const items = [
      itemAt('2024-01-01T09:15:00'),
      itemAt('2024-06-15T09:45:00'),
      itemAt('2024-03-10T23:00:00'),
    ];

    const result = buildHourlyActivity(items);

    expect(result[9].count).toBe(2);
    expect(result[23].count).toBe(1);
    expect(result.reduce((sum, b) => sum + b.count, 0)).toBe(3);
  });

  it('is indexed 0-23 in order', () => {
    const result = buildHourlyActivity([]);
    expect(result.map((b) => b.hour)).toEqual(Array.from({ length: 24 }, (_, i) => i));
  });
});

describe('buildMonthlyActivity', () => {
  it('returns an empty array for an empty/missing list', () => {
    expect(buildMonthlyActivity([])).toEqual([]);
    expect(buildMonthlyActivity(undefined)).toEqual([]);
  });

  it('buckets items by calendar month', () => {
    const items = [
      itemAt('2024-01-05T00:00:00'),
      itemAt('2024-01-20T00:00:00'),
      itemAt('2024-03-01T00:00:00'),
    ];

    const result = buildMonthlyActivity(items);

    expect(result).toEqual([
      { month: '2024-01', count: 2 },
      { month: '2024-02', count: 0 },
      { month: '2024-03', count: 1 },
    ]);
  });

  it('fills a dormant stretch spanning a year boundary with zero-count months', () => {
    const items = [itemAt('2023-11-15T00:00:00'), itemAt('2024-02-01T00:00:00')];

    const result = buildMonthlyActivity(items);

    expect(result.map((b) => b.month)).toEqual([
      '2023-11', '2023-12', '2024-01', '2024-02',
    ]);
    expect(result[0].count).toBe(1);
    expect(result[1].count).toBe(0);
    expect(result[2].count).toBe(0);
    expect(result[3].count).toBe(1);
  });

  it('handles a single month with no gap-filling needed', () => {
    const items = [itemAt('2024-05-01T00:00:00'), itemAt('2024-05-20T00:00:00')];

    expect(buildMonthlyActivity(items)).toEqual([{ month: '2024-05', count: 2 }]);
  });
});

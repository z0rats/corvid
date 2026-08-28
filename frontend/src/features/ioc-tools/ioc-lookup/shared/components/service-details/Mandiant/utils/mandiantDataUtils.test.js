import {
  processSourcesForDisplay,
  buildCategoryStats,
  buildTimelineData,
  transformCategoryDataForPie,
} from './mandiantDataUtils';

describe('processSourcesForDisplay', () => {
  it('returns an empty array when there are no sources', () => {
    expect(processSourcesForDisplay(null)).toEqual([]);
    expect(processSourcesForDisplay([])).toEqual([]);
  });

  it('groups sources by name and merges their categories', () => {
    const result = processSourcesForDisplay([
      { source_name: 'FeedX', category: ['malware'], first_seen: '2024-01-01', last_seen: '2024-01-05' },
      { source_name: 'FeedX', category: ['c2'], first_seen: '2024-01-02', last_seen: '2024-01-10' },
    ]);

    expect(result).toHaveLength(1);
    expect(result[0].source_name).toBe('FeedX');
    expect(result[0].category.sort()).toEqual(['c2', 'malware']);
    expect(result[0].first_seen).toBe('2024-01-01');
    expect(result[0].last_seen).toBe('2024-01-10');
  });
});

describe('buildCategoryStats', () => {
  it('counts occurrences of each category across all indicator sources', () => {
    const result = buildCategoryStats([
      { sources: [{ category: ['malware', 'c2'] }] },
      { sources: [{ category: ['malware'] }] },
    ]);

    expect(result).toEqual({ malware: 2, c2: 1 });
  });

  it('returns an empty object when there are no indicators', () => {
    expect(buildCategoryStats([])).toEqual({});
  });
});

describe('buildTimelineData', () => {
  it('buckets indicators by first-seen month and sorts chronologically', () => {
    const result = buildTimelineData([
      { first_seen: '2024-02-15' },
      { first_seen: '2024-01-10' },
      { first_seen: '2024-01-20' },
    ]);

    expect(result).toHaveLength(2);
    expect(result[0]).toMatchObject({ month: 0, year: 2024, count: 2 });
    expect(result[1]).toMatchObject({ month: 1, year: 2024, count: 1 });
  });

  it('ignores indicators with no first_seen', () => {
    expect(buildTimelineData([{}])).toEqual([]);
  });
});

describe('transformCategoryDataForPie', () => {
  it('returns a No Data placeholder when categoryStats is empty', () => {
    expect(transformCategoryDataForPie({})).toEqual([{ id: 'No Data', label: 'No Data', value: 1 }]);
  });

  it('maps each category to a pie entry', () => {
    expect(transformCategoryDataForPie({ malware: 3 })).toEqual([
      { id: 'malware', label: 'malware', value: 3 },
    ]);
  });
});

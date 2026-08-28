import { transformDataForPie, transformDataForMap, buildScoreData } from './crowdSecDataUtils';

describe('transformDataForPie', () => {
  it('maps each country entry to a {id, label, value} object', () => {
    expect(transformDataForPie({ US: 10, FR: 3 })).toEqual([
      { id: 'US', label: 'US', value: 10 },
      { id: 'FR', label: 'FR', value: 3 },
    ]);
  });

  it('returns an empty array for falsy input', () => {
    expect(transformDataForPie(null)).toEqual([]);
    expect(transformDataForPie(undefined)).toEqual([]);
  });
});

describe('transformDataForMap', () => {
  it('maps a known ISO-2 code to its ISO-3 equivalent', () => {
    expect(transformDataForMap({ US: 10 })).toEqual([{ id: 'USA', value: 10 }]);
  });

  it('falls back to the raw key for an unmapped code', () => {
    expect(transformDataForMap({ ZZ: 5 })).toEqual([{ id: 'ZZ', value: 5 }]);
  });

  it('returns an empty array for falsy input', () => {
    expect(transformDataForMap(null)).toEqual([]);
  });
});

describe('buildScoreData', () => {
  it('builds one entry per period from the nested scores object', () => {
    const result = buildScoreData({
      scores: {
        overall: { aggressiveness: 1, threat: 2, trust: 3, anomaly: 4, total: 5 },
        last_day: { aggressiveness: 1 },
      },
    });

    expect(result).toEqual([
      { name: 'Overall', aggressiveness: 1, threat: 2, trust: 3, anomaly: 4, total: 5 },
      { name: 'Last Day', aggressiveness: 1, threat: 0, trust: 0, anomaly: 0, total: 0 },
      { name: 'Last Week', aggressiveness: 0, threat: 0, trust: 0, anomaly: 0, total: 0 },
      { name: 'Last Month', aggressiveness: 0, threat: 0, trust: 0, anomaly: 0, total: 0 },
    ]);
  });

  it('defaults every score to 0 when scores is missing entirely', () => {
    const result = buildScoreData({});
    expect(result[0]).toEqual({
      name: 'Overall',
      aggressiveness: 0,
      threat: 0,
      trust: 0,
      anomaly: 0,
      total: 0,
    });
  });
});

/**
 * Groups and deduplicates indicator sources by source name
 */
export function processSourcesForDisplay(sources) {
  if (!sources || sources.length === 0) return [];

  const groupedSources = {};
  sources.forEach(source => {
    const name = source.source_name;
    if (!groupedSources[name]) {
      groupedSources[name] = {
        source_name: name,
        categories: new Set(),
        first_seen: source.first_seen,
        last_seen: source.last_seen,
      };
    }
    source.category?.forEach(cat => groupedSources[name].categories.add(cat));
    if (source.first_seen && new Date(source.first_seen) < new Date(groupedSources[name].first_seen)) {
      groupedSources[name].first_seen = source.first_seen;
    }
    if (source.last_seen && new Date(source.last_seen) > new Date(groupedSources[name].last_seen)) {
      groupedSources[name].last_seen = source.last_seen;
    }
  });

  return Object.values(groupedSources).map(src => ({
    ...src,
    category: Array.from(src.categories),
  }));
}

/**
 * Builds category statistics from indicators
 */
export function buildCategoryStats(indicators) {
  const categories = {};
  indicators.forEach(indicator => {
    indicator.sources?.forEach(source => {
      source.category?.forEach(cat => {
        categories[cat] = (categories[cat] || 0) + 1;
      });
    });
  });
  return categories;
}

/**
 * Builds timeline data from indicators for line chart
 */
export function buildTimelineData(indicators) {
  const timeline = [];
  indicators.forEach(indicator => {
    if (indicator.first_seen) {
      const firstSeen = new Date(indicator.first_seen);
      const month = firstSeen.getMonth();
      const year = firstSeen.getFullYear();
      const entry = timeline.find(e => e.month === month && e.year === year);
      if (entry) {
        entry.count += 1;
      } else {
        timeline.push({
          month,
          year,
          count: 1,
          date: `${firstSeen.toLocaleString('default', { month: 'short' })} ${year}`,
        });
      }
    }
  });

  const sorted = timeline.sort((a, b) => a.year !== b.year ? a.year - b.year : a.month - b.month);
  return [{
    id: 'indicators',
    color: 'hsl(210, 70%, 50%)',
    data: sorted.map(item => ({ x: item.date, y: item.count })),
  }];
}

/**
 * Transforms category stats into Nivo pie chart format
 */
export function transformCategoryDataForPie(categoryStats) {
  if (Object.keys(categoryStats).length === 0) {
    return [{ id: 'No Data', label: 'No Data', value: 1 }];
  }
  return Object.keys(categoryStats).map(key => ({
    id: key,
    label: key,
    value: categoryStats[key],
  }));
}

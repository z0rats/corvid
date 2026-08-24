const MS_PER_SECOND = 1000;

function toMonthKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

export function buildHourlyActivity(items) {
  const counts = new Array(24).fill(0);
  (items || []).forEach((item) => {
    const hour = new Date(item.created_utc * MS_PER_SECOND).getHours();
    counts[hour] += 1;
  });
  return counts.map((count, hour) => ({ hour, count }));
}

// Fills every month between the first and last observed post/comment with a
// zero-count entry (not just the months that actually have data) - a bar
// chart with a real gap of zero-height bars is what makes a dormant stretch
// visible; skipping empty months would just silently compress the timeline.
export function buildMonthlyActivity(items) {
  const counts = new Map();
  (items || []).forEach((item) => {
    const key = toMonthKey(new Date(item.created_utc * MS_PER_SECOND));
    counts.set(key, (counts.get(key) || 0) + 1);
  });

  if (counts.size === 0) return [];

  const keys = [...counts.keys()].sort();
  let [year, month] = keys[0].split('-').map(Number);
  const [lastYear, lastMonth] = keys[keys.length - 1].split('-').map(Number);

  const result = [];
  while (year < lastYear || (year === lastYear && month <= lastMonth)) {
    const key = `${year}-${String(month).padStart(2, '0')}`;
    result.push({ month: key, count: counts.get(key) || 0 });
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }
  return result;
}

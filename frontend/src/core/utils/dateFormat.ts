const RELATIVE_UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 365 * 24 * 3600],
  ['month', 30 * 24 * 3600],
  ['week', 7 * 24 * 3600],
  ['day', 24 * 3600],
  ['hour', 3600],
  ['minute', 60],
];

/** "3 hours ago" / "in 2 days" / "now" (under a minute), rounded to the largest whole unit. */
export function formatRelativeTime(date: Date, now: Date = new Date(), locale = 'en'): string {
  const seconds = (date.getTime() - now.getTime()) / 1000;
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
  for (const [unit, size] of RELATIVE_UNITS) {
    // Round the magnitude: Math.round(-1.5) is -1, which would make "90s ago" read "1 minute ago".
    if (Math.abs(seconds) >= size) return rtf.format(Math.sign(seconds) * Math.round(Math.abs(seconds) / size), unit);
  }
  return rtf.format(0, 'second');
}

/** "October 18, 2026, 3:04 PM" in the viewer's time zone. */
export function formatDateTime(date: Date, locale = 'en-US'): string {
  const day = date.toLocaleDateString(locale, { month: 'long', day: 'numeric', year: 'numeric' });
  const time = date.toLocaleTimeString(locale, { hour: 'numeric', minute: '2-digit' });
  return `${day}, ${time}`;
}

const ISO_DURATION_RE = /^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/;

/** Formats an ISO 8601 duration (e.g. "PT1H3M33S") as "1:03:33"/"3:33"; returns null if unparseable. */
export function formatIsoDuration(isoDuration) {
  const match = ISO_DURATION_RE.exec(isoDuration ?? '');
  if (!match) return null;

  const hours = Number(match[1] ?? 0);
  const minutes = Number(match[2] ?? 0);
  const seconds = Number(match[3] ?? 0);
  if (!hours && !minutes && !seconds) return null;

  const parts = hours > 0
    ? [hours, String(minutes).padStart(2, '0'), String(seconds).padStart(2, '0')]
    : [minutes, String(seconds).padStart(2, '0')];
  return parts.join(':');
}

/** Formats a numeric-string count (e.g. view/like/comment count) with thousands separators. */
export function formatCount(value) {
  const num = Number(value);
  if (value === null || value === undefined || Number.isNaN(num)) return null;
  return new Intl.NumberFormat().format(num);
}

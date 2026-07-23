/**
 * Returns true if `latest` is a strictly newer version than `current`.
 * Compares dot-separated numeric parts (e.g. "2.0.3" vs "2.0.10"); falls back
 * to false for anything that doesn't parse as numeric version parts.
 */
export function isNewerVersion(current, latest) {
  if (!current || !latest) return false;

  const currentParts = current.split('.').map(Number);
  const latestParts = latest.split('.').map(Number);

  if (currentParts.some(Number.isNaN) || latestParts.some(Number.isNaN)) {
    return false;
  }

  const length = Math.max(currentParts.length, latestParts.length);
  for (let i = 0; i < length; i += 1) {
    const currentPart = currentParts[i] || 0;
    const latestPart = latestParts[i] || 0;
    if (latestPart > currentPart) return true;
    if (latestPart < currentPart) return false;
  }
  return false;
}

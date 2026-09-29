/** Epoch seconds -> localized date, or null when absent. */
export function formatEpoch(seconds) {
  if (!seconds) return null;
  return new Date(seconds * 1000).toLocaleDateString();
}

/** "City, State, Country" from the resolved names, falling back to the raw codes. */
export function formatLocation(location) {
  if (!location) return null;
  const parts = [
    location.city,
    location.state,
    location.country || location.country_code,
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(', ') : null;
}

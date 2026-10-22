const compactFormatter = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 });

/** 10287298 -> "10.3M"; null/undefined -> null. */
export function formatCompact(value) {
  if (value == null) return null;
  return compactFormatter.format(value);
}

/** 0.2534 -> "25%"; null/undefined -> null. */
export function formatPercent(ratio) {
  if (ratio == null) return null;
  return `${Math.round(ratio * 100)}%`;
}

/** ISO timestamp -> localized date, or null. */
export function formatDate(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString();
}

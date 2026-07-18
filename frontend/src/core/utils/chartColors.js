// Validated categorical palette (8 hues, fixed order — CVD-safe adjacency in both modes).
const CATEGORICAL_LIGHT = ['#2a78d6', '#008300', '#e87ba4', '#eda100', '#1baf7a', '#eb6834', '#4a3aa7', '#e34948'];
const CATEGORICAL_DARK = ['#3987e5', '#008300', '#d55181', '#c98500', '#199e70', '#d95926', '#9085e9', '#e66767'];

export const MAX_CATEGORICAL_SLOTS = CATEGORICAL_LIGHT.length;

export function getCategoricalPalette(theme) {
  return theme.palette.mode === 'dark' ? CATEGORICAL_DARK : CATEGORICAL_LIGHT;
}

export function getCategoricalColor(theme, index) {
  const palette = getCategoricalPalette(theme);
  return palette[index % palette.length];
}

/**
 * Caps a list of {id, label, value} entries to the categorical palette size,
 * folding the smallest remainder into a single "Other" entry.
 */
export function foldExcessCategories(entries, otherLabel) {
  if (entries.length <= MAX_CATEGORICAL_SLOTS) return entries;

  const sorted = [...entries].sort((a, b) => b.value - a.value);
  const head = sorted.slice(0, MAX_CATEGORICAL_SLOTS - 1);
  const tail = sorted.slice(MAX_CATEGORICAL_SLOTS - 1);
  const otherValue = tail.reduce((sum, entry) => sum + (entry.value || 0), 0);

  return [...head, { id: 'other', label: otherLabel, value: otherValue }];
}

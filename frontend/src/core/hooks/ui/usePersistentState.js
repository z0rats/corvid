import { useEffect, useState } from 'react';

const read = (key, initial, validate) => {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return initial;
    const value = JSON.parse(raw);
    return validate(value) ? value : initial;
  } catch {
    return initial;
  }
};

/**
 * useState that survives reloads via localStorage - for per-browser UI preferences (panel
 * widths, collapsed state). A stored value failing `validate` (or unreadable storage) falls
 * back to `initial`.
 */
export function usePersistentState(key, initial, validate = () => true) {
  const [value, setValue] = useState(() => read(key, initial, validate));

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Storage full or blocked (private mode) - the preference just won't persist.
    }
  }, [key, value]);

  return [value, setValue];
}

import { useEffect, useState } from 'react';
import TextField from '@mui/material/TextField';

/**
 * A settings field that saves on blur/Enter instead of on every keystroke.
 *
 * Saving per keystroke sends every intermediate value (1, 12, 120), and for a controlled
 * `type="number"` field it also makes decimals untypeable: a half-typed "0." reads back as 0,
 * the saved 0 re-renders the field, and the "." is gone. The draft lives here until committed;
 * an empty or non-numeric number draft reverts to the saved value instead of saving 0.
 */
export default function CommitTextField({ value, onCommit, type, onBlur, onKeyDown, ...props }) {
  const saved = value ?? '';
  const [draft, setDraft] = useState(saved);
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    if (!focused) setDraft(saved);
  }, [saved, focused]);

  const commit = () => {
    if (type === 'number') {
      const text = String(draft).trim();
      const parsed = Number(text);
      if (text === '' || !Number.isFinite(parsed)) {
        setDraft(saved);
        return;
      }
      if (parsed !== value) onCommit(parsed);
      return;
    }
    if (draft !== saved) onCommit(draft);
  };

  return (
    <TextField
      {...props}
      type={type}
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onFocus={() => setFocused(true)}
      onBlur={(e) => {
        setFocused(false);
        commit();
        onBlur?.(e);
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          commit();
        }
        onKeyDown?.(e);
      }}
    />
  );
}

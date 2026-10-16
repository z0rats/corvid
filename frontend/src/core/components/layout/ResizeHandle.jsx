import Box from '@mui/material/Box';

const KEYBOARD_STEP = 16;

/**
 * Drag handle on a side panel's right edge - a focusable `separator` so the width can also be
 * changed with the keyboard (←/→ in steps, Home/End for min/max). Dragging is the caller's
 * pointer tracking (Layout.jsx owns the document-level listeners); pointer events rather than
 * mouse ones so it works with touch and pens too.
 */
export default function ResizeHandle({ label, value, min, max, onPointerDown, onChange }) {
  const handleKeyDown = (event) => {
    const next = {
      ArrowLeft: value - KEYBOARD_STEP,
      ArrowRight: value + KEYBOARD_STEP,
      Home: min,
      End: max,
    }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    onChange(Math.min(max, Math.max(min, next)));
  };

  return (
    <Box
      role="separator"
      aria-orientation="vertical"
      aria-label={label}
      aria-valuenow={value}
      aria-valuemin={min}
      aria-valuemax={max}
      tabIndex={0}
      onPointerDown={onPointerDown}
      onKeyDown={handleKeyDown}
      sx={{
        position: 'absolute',
        top: 0,
        right: 0,
        bottom: 0,
        width: 6,
        cursor: 'col-resize',
        touchAction: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        outline: 'none',
        '&::after': {
          content: '""',
          width: 2,
          height: 32,
          borderRadius: 1,
          bgcolor: 'divider',
          transition: 'background-color 0.2s, height 0.2s',
        },
        '&:hover::after, &:focus-visible::after': {
          bgcolor: 'primary.main',
          height: 48,
        },
      }}
    />
  );
}

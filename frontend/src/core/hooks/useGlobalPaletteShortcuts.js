import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

// Dispatched by Layout.jsx's AppBar search-trigger button — the palette's open state is owned
// entirely inside useCommandPalette (only instantiated in CommandPalette.jsx), so opening it from
// elsewhere in the tree goes through a DOM event rather than lifting state up.
export const OPEN_COMMAND_PALETTE_EVENT = 'corvid:open-command-palette';

const EDITABLE_TAG_NAMES = new Set(['INPUT', 'TEXTAREA', 'SELECT']);

function isEditableTarget(el) {
  if (!el) return false;
  if (EDITABLE_TAG_NAMES.has(el.tagName)) return true;
  return Boolean(el.isContentEditable);
}

/**
 * Global keyboard/paste listeners for the command palette — active regardless of whether the
 * palette itself is mounted open. Palette-local key grammar (arrow nav, Enter, the recording
 * shortcuts, etc.) lives in useCommandPalette's handlePaletteKeyDown instead.
 */
export function useGlobalPaletteShortcuts(isOpen, open, close, onShowShortcutSheet) {
  const navigate = useNavigate();
  const location = useLocation();

  // Global `/`, Cmd/Ctrl+K, Cmd/Ctrl+, and `?` listener — guarded against hijacking focused
  // text inputs. Cmd/Ctrl+, works regardless of open state, like every other app's preferences
  // shortcut; the rest only fire while closed to avoid fighting the palette's own key handling.
  useEffect(() => {
    const handler = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === ',') {
        event.preventDefault();
        navigate('/settings');
        if (isOpen) close();
        return;
      }
      if (isOpen) return;
      const target = event.target;
      if (event.key === '/' && !isEditableTarget(target)) {
        event.preventDefault();
        open();
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        open();
        return;
      }
      if (event.key === '?' && !isEditableTarget(target)) {
        event.preventDefault();
        onShowShortcutSheet();
      }
    };
    // StartScreen dispatches this with a `detail.query` payload when it hands off a
    // modal-only grammar kind (record/playbook) it deliberately doesn't implement itself —
    // Layout.jsx's own trigger dispatches a plain Event, so `detail` is undefined there.
    const handleOpenEvent = (event) => { if (!isOpen) open(event?.detail?.query ?? ''); };

    window.addEventListener('keydown', handler);
    window.addEventListener(OPEN_COMMAND_PALETTE_EVENT, handleOpenEvent);
    return () => {
      window.removeEventListener('keydown', handler);
      window.removeEventListener(OPEN_COMMAND_PALETTE_EVENT, handleOpenEvent);
    };
  }, [isOpen, open, close, navigate, onShowShortcutSheet]);

  // Global ⌘V/Ctrl+V — a pasted image jumps to Image Tools with it preloaded, from anywhere in
  // the app (see docs/command-palette-plan.md's Keyboard shortcuts table). Image Tools' own
  // `/image-tools` page has its own local paste handler already, so this one steps aside there
  // to avoid double-handling the same clipboard event.
  useEffect(() => {
    const handlePaste = (event) => {
      if (location.pathname.startsWith('/image-tools')) return;
      const items = event.clipboardData?.items;
      if (!items) return;
      const imageItem = Array.from(items).find((item) => item.type.startsWith('image/'));
      if (!imageItem) return;
      const file = imageItem.getAsFile();
      if (!file) return;

      event.preventDefault();
      if (isOpen) close();
      navigate('/image-tools', { state: { file } });
    };
    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [location.pathname, isOpen, close, navigate]);
}

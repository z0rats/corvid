/**
 * Cascading clipboard write that also works on plain-HTTP deployments (Corvid's default —
 * HSTS is production-only, see CLAUDE.md), where navigator.clipboard is unavailable because
 * it requires a secure context. Falls back to the deprecated but still-functional
 * document.execCommand('copy') path, and reports failure so the caller can show the value
 * pre-selected for a manual Ctrl+C instead of silently doing nothing.
 */
export async function copyToClipboard(text) {
  if (window.isSecureContext && navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // permission denied or similar — fall through to the legacy path
    }
  }
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  let ok;
  try {
    ok = document.execCommand('copy');
  } catch {
    ok = false;
  }
  document.body.removeChild(textarea);
  return ok;
}

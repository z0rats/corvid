// Bracketed defang markers only - a bare " dot " / " at " is too ambiguous to undo in free text.
const DOT_RE = /\[\.\]|\(\.\)|\{\.\}|\[dot\]|\(dot\)|\{dot\}/gi;
const AT_RE = /\[@\]|\(@\)|\{@\}|\[at\]|\(at\)|\{at\}/gi;
const COLON_SLASH_RE = /\[:\/\/\]|\[:\]\/\//g;
const COLON_RE = /\[:\]/g;
const SCHEME_RE = /^h[x]{2}p(s?)(?=:|\[:)/i;
const FXP_RE = /^fxp(?=:|\[:)/i;

/**
 * Client-side refang for a single pasted indicator, so `1.2.3[.]4` or `hxxps[://]evil[.]com`
 * copied out of a threat report is looked up as-is instead of being rejected as an unknown
 * type. The Defang/Fang tool (`/api/defang/`) stays the full-featured round-trip; this only
 * undoes the common bracketed markers.
 */
export function refang(value: string): string {
  return value
    .trim()
    .replace(SCHEME_RE, 'http$1')
    .replace(FXP_RE, 'ftp')
    .replace(COLON_SLASH_RE, '://')
    .replace(COLON_RE, ':')
    .replace(DOT_RE, '.')
    .replace(AT_RE, '@');
}

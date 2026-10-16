// How to write the Cmd/Ctrl modifier in UI hints: macOS users press ⌘, everyone else Ctrl.
export const MOD_KEY_LABEL = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.userAgent) ? '⌘' : 'Ctrl+';

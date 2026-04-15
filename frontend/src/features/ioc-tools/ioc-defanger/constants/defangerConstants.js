export const SUPPORTED_DEFANGING_TECHNIQUES = [
  { title: "Dots", description: "[.] (.) {.} [dot] (dot) {dot} \\. \" . \"" },
  { title: "Protocols", description: " hxxp hxxps fxp" },
  { title: "Seperators", description: "[:] [://] [/] [@] [at]" },
  { title: "IOCs", description: "Domains, IPs, URLs, Emails, Hashes" },
];

export const TYPE_COLOR_MAP = {
  'IP Address': 'primary',
  'Domain': 'secondary',
  'URL': 'success',
  'Email': 'warning',
  'MD5 Hash': 'info',
  'SHA1 Hash': 'info',
  'SHA256 Hash': 'info',
  'CVE': 'error',
  'Unknown': 'default',
};

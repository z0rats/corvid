// Compact hand-rolled port of frontend/src/core/utils/iocTypeDetection.js's detectIocType,
// extended with a Phone type for the selection-based context menu (Corvid's own IOC vocabulary
// has no phone lookups, but labeling the match is still useful — the item still opens IOC
// lookup like everything else). Duplicated by hand, not shared code — the extension has no
// build step to import from frontend/. Loaded via importScripts() in background.js.

const IOC_PATTERNS = {
  MD5: /^[a-f0-9]{32}$/i,
  SHA1: /^[a-f0-9]{40}$/i,
  SHA256: /^[a-f0-9]{64}$/i,
  IPv4: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  IPv6: /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$/i,
  CVE: /^CVE-[0-9]{4}-[0-9]{4,}$/i,
  URL: /^(?:https?|ftp):\/\/\S+$/i,
  Domain: /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$/,
  Email: /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
};

const PHONE_PATTERN = /^\+?[1-9]\d{6,14}$/;

function isLikelyPhone(value) {
  return PHONE_PATTERN.test(value.replace(/[\s\-().]/g, ''));
}

// Order matters: hashes/addresses before IP, IP before phone, phone before URL/domain/email
// (a bare-digit selection should read as a phone number, not fall through to "unknown").
function detectIocType(rawValue) {
  const value = (rawValue ?? '').trim().replace(/[.,;:!?)\]}'"]+$/, '');
  if (!value) return null;

  if (IOC_PATTERNS.MD5.test(value)) return 'MD5';
  if (IOC_PATTERNS.SHA1.test(value)) return 'SHA1';
  if (IOC_PATTERNS.SHA256.test(value)) return 'SHA256';
  if (IOC_PATTERNS.IPv4.test(value)) return 'IPv4';
  if (IOC_PATTERNS.IPv6.test(value)) return 'IPv6';
  if (isLikelyPhone(value)) return 'Phone';
  if (IOC_PATTERNS.CVE.test(value)) return 'CVE';
  if (IOC_PATTERNS.URL.test(value)) return 'URL';
  if (IOC_PATTERNS.Domain.test(value)) return 'Domain';
  if (IOC_PATTERNS.Email.test(value)) return 'Email';
  return null;
}

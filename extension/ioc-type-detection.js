// Wrapper around the shared IOC-type regex table in generated-ioc-patterns.js (generated from
// frontend/src/core/utils/iocTypeDetection.ts's IOC_TYPE_PATTERNS — see that file's own header),
// extended with a Phone type for the selection-based context menu (Corvid's own IOC vocabulary
// has no phone lookups, but labeling the match is still useful — the item still opens IOC lookup
// like everything else) and trailing-punctuation stripping (needed for text selected on a page).
// generated-ioc-patterns.js loads first everywhere ioc-type-detection.js does (manifest.json's
// content_scripts, sidepanel.html, background.js's importScripts), so IOC_PATTERNS below is
// just that file's GENERATED_IOC_TYPE_PATTERNS global; the require() branch only runs under
// Node/Vitest, which has no shared script scope to read a preceding <script> tag's globals from.

let IOC_PATTERNS = typeof GENERATED_IOC_TYPE_PATTERNS !== 'undefined' ? GENERATED_IOC_TYPE_PATTERNS : undefined;
if (typeof module !== 'undefined' && module.exports) {
  IOC_PATTERNS = require('./generated-ioc-patterns.js').GENERATED_IOC_TYPE_PATTERNS;
}

const PHONE_PATTERN = /^\+?[1-9]\d{6,14}$/;

function isLikelyPhone(value) {
  return PHONE_PATTERN.test(value.replace(/[\s\-().]/g, ''));
}

// Order matters: hashes/crypto addresses before IP (same priority as iocTypeDetection.ts), IP
// before phone, phone before URL/domain/email (a bare-digit selection should read as a phone
// number, not fall through to "unknown").
function detectIocType(rawValue) {
  const value = (rawValue ?? '').trim().replace(/[.,;:!?)\]}'"]+$/, '');
  if (!value) return null;

  if (IOC_PATTERNS.MD5.test(value)) return 'MD5';
  if (IOC_PATTERNS.SHA1.test(value)) return 'SHA1';
  if (IOC_PATTERNS.SHA256.test(value)) return 'SHA256';
  if (IOC_PATTERNS.EVMAddress.test(value)) return 'EVMAddress';
  if (IOC_PATTERNS.BitcoinAddress.test(value)) return 'BitcoinAddress';
  if (IOC_PATTERNS.TronAddress.test(value)) return 'TronAddress';
  if (IOC_PATTERNS.XRPAddress.test(value)) return 'XRPAddress';
  if (IOC_PATTERNS.DogecoinAddress.test(value)) return 'DogecoinAddress';
  if (IOC_PATTERNS.CardanoAddress.test(value)) return 'CardanoAddress';
  if (IOC_PATTERNS.LitecoinAddress.test(value)) return 'LitecoinAddress';
  if (IOC_PATTERNS.StellarAddress.test(value)) return 'StellarAddress';
  if (IOC_PATTERNS.BinanceChainAddress.test(value)) return 'BinanceChainAddress';
  if (IOC_PATTERNS.LiskAddress.test(value)) return 'LiskAddress';
  if (IOC_PATTERNS.IPv4.test(value)) return 'IPv4';
  if (IOC_PATTERNS.IPv6.test(value)) return 'IPv6';
  if (isLikelyPhone(value)) return 'Phone';
  if (IOC_PATTERNS.CVE.test(value)) return 'CVE';
  if (IOC_PATTERNS.URL.test(value)) return 'URL';
  if (IOC_PATTERNS.Domain.test(value)) return 'Domain';
  if (IOC_PATTERNS.Email.test(value)) return 'Email';
  return null;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { detectIocType };
}

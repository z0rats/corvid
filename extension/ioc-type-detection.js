// Compact hand-rolled port of frontend/src/core/utils/iocTypeDetection.ts's detectIocType,
// extended with a Phone type for the selection-based context menu (Corvid's own IOC vocabulary
// has no phone lookups, but labeling the match is still useful — the item still opens IOC
// lookup like everything else). Duplicated by hand, not shared code — the extension has no
// build step to import from frontend/, and isn't covered by the testdata/ioc-type-detection-cases.json
// fixture the backend/frontend copies share (see docs/architecture/command-palette.md) — re-check
// this against iocTypeDetection.ts's IOC_TYPE_PATTERNS by hand when that file changes.

const IOC_PATTERNS = {
  MD5: /^[a-f0-9]{32}$/i,
  SHA1: /^[a-f0-9]{40}$/i,
  SHA256: /^[a-f0-9]{64}$/i,
  EVMAddress: /^0x[a-f0-9]{40}$/i,
  BitcoinAddress: /^(1[a-zA-Z0-9]{25,34}|3[a-zA-Z0-9]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{25,90})$/,
  TronAddress: /^T[a-zA-Z0-9]{33}$/,
  XRPAddress: /^r[a-zA-Z0-9]{24,34}$/,
  DogecoinAddress: /^D[a-zA-Z0-9]{25,33}$/,
  CardanoAddress: /^Ddz[a-zA-Z0-9]{90,110}$/,
  LitecoinAddress: /^L[a-zA-Z0-9]{25,34}$/,
  StellarAddress: /^[GS][A-Z2-7]{54,58}$/,
  BinanceChainAddress: /^bnb1[a-z0-9]{38}$/,
  LiskAddress: /^[0-9]{1,20}L$/,
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

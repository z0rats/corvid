// GENERATED FILE - DO NOT EDIT BY HAND.
// Regenerate with: node frontend/scripts/generate-extension-ioc-patterns.js
// Source of truth: frontend/src/core/utils/iocTypeDetection.ts's IOC_TYPE_PATTERNS.
// A pre-commit hook regenerates this automatically when that file changes; CI fails if
// this file is stale (see docs/architecture/browser-extension.md).

const GENERATED_IOC_TYPE_PATTERNS = {
  MD5: /^[a-f0-9]{32}$/i,
  SHA1: /^[a-f0-9]{40}$/i,
  SHA256: /^[a-f0-9]{64}$/i,
  IPv4: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  IPv6: /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$/i,
  URL: /^(?:(?:https?|ftp):\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:[a-z¡-￿0-9](?:[a-z¡-￿0-9-]*[a-z¡-￿0-9])?)(?:\.[a-z¡-￿0-9](?:[a-z¡-￿0-9-]*[a-z¡-￿0-9])?)*(?:\.(?:[a-z¡-￿]{2,}))\.?)(?::\d{2,5})?(?:[/?#]\S*)?$/i,
  Domain: /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$/,
  Email: /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
  CVE: /^CVE-[0-9]{4}-[0-9]{4,}$/i,
  EVMAddress: /^0x[a-f0-9]{40}$/i,
  BitcoinAddress: /^(1[a-zA-Z0-9]{25,34}|3[a-zA-Z0-9]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{25,90})$/,
  TronAddress: /^T[a-zA-Z0-9]{33}$/,
  XRPAddress: /^r[a-zA-Z0-9]{24,34}$/,
  DogecoinAddress: /^D[a-zA-Z0-9]{25,33}$/,
  LitecoinAddress: /^L[a-zA-Z0-9]{25,34}$/,
  StellarAddress: /^[GS][A-Z2-7]{54,58}$/,
  BinanceChainAddress: /^bnb1[a-z0-9]{38}$/,
  LiskAddress: /^[0-9]{1,20}L$/,
  CardanoAddress: /^Ddz[a-zA-Z0-9]{90,110}$/,
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { GENERATED_IOC_TYPE_PATTERNS };
}

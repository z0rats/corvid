/**
 * JS port of backend/app/features/ioc_tools/ioc_lookup/single_lookup/utils/ioc_utils.py's
 * IOC_TYPE_PATTERNS/determine_ioc_type. Same priority order and return strings, verified against
 * the same fixture (testdata/ioc-type-detection-cases.json) as the backend's own test, so the two
 * can't silently diverge.
 */

export const IOC_TYPES = {
  IPV4: 'IPv4',
  IPV6: 'IPv6',
  MD5: 'MD5',
  SHA1: 'SHA1',
  SHA256: 'SHA256',
  URL: 'URL',
  DOMAIN: 'Domain',
  EMAIL: 'Email',
  CVE: 'CVE',
  EVM_ADDRESS: 'EVMAddress',
  BITCOIN_ADDRESS: 'BitcoinAddress',
  UNKNOWN: 'unknown',
};

const IOC_TYPE_PATTERNS = {
  [IOC_TYPES.MD5]: /^[a-f0-9]{32}$/i,
  [IOC_TYPES.SHA1]: /^[a-f0-9]{40}$/i,
  [IOC_TYPES.SHA256]: /^[a-f0-9]{64}$/i,
  [IOC_TYPES.IPV4]: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  [IOC_TYPES.IPV6]: /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$/i,
  [IOC_TYPES.URL]: /^(?:(?:https?|ftp):\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:[a-z¡-￿0-9](?:[a-z¡-￿0-9-]*[a-z¡-￿0-9])?)(?:\.[a-z¡-￿0-9](?:[a-z¡-￿0-9-]*[a-z¡-￿0-9])?)*(?:\.(?:[a-z¡-￿]{2,}))\.?)(?::\d{2,5})?(?:[/?#]\S*)?$/i,
  [IOC_TYPES.DOMAIN]: /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$/,
  [IOC_TYPES.EMAIL]: /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
  [IOC_TYPES.CVE]: /^CVE-[0-9]{4}-[0-9]{4,}$/i,
  [IOC_TYPES.EVM_ADDRESS]: /^0x[a-f0-9]{40}$/i,
  [IOC_TYPES.BITCOIN_ADDRESS]: /^(1[a-zA-Z0-9]{25,34}|3[a-zA-Z0-9]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{25,90})$/,
};

/**
 * Determines the type of an Indicator of Compromise (IOC).
 * The order of checks is important to prevent misclassification (e.g., URL before Domain).
 */
export function detectIocType(rawValue) {
  const value = (rawValue ?? '').trim();

  if (IOC_TYPE_PATTERNS[IOC_TYPES.MD5].test(value)) return IOC_TYPES.MD5;
  if (IOC_TYPE_PATTERNS[IOC_TYPES.SHA1].test(value)) return IOC_TYPES.SHA1;
  if (IOC_TYPE_PATTERNS[IOC_TYPES.SHA256].test(value)) return IOC_TYPES.SHA256;

  if (IOC_TYPE_PATTERNS[IOC_TYPES.EVM_ADDRESS].test(value)) return IOC_TYPES.EVM_ADDRESS;
  if (IOC_TYPE_PATTERNS[IOC_TYPES.BITCOIN_ADDRESS].test(value)) return IOC_TYPES.BITCOIN_ADDRESS;

  if (IOC_TYPE_PATTERNS[IOC_TYPES.IPV4].test(value)) return IOC_TYPES.IPV4;
  if (IOC_TYPE_PATTERNS[IOC_TYPES.IPV6].test(value)) return IOC_TYPES.IPV6;

  if (IOC_TYPE_PATTERNS[IOC_TYPES.CVE].test(value)) return IOC_TYPES.CVE;

  if (IOC_TYPE_PATTERNS[IOC_TYPES.URL].test(value)) return IOC_TYPES.URL;
  if (IOC_TYPE_PATTERNS[IOC_TYPES.DOMAIN].test(value)) return IOC_TYPES.DOMAIN;

  if (IOC_TYPE_PATTERNS[IOC_TYPES.EMAIL].test(value)) return IOC_TYPES.EMAIL;

  return IOC_TYPES.UNKNOWN;
}

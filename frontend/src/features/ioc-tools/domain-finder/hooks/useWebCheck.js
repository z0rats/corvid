import { useDomainPanel } from './useDomainPanel';

// The four web-check sub-checks (SSL, security headers, DNSSEC, blocklist) are shown as one
// "Web Check" panel, but each is its own panel request with independent loading/error
// state - one slow or failing check shouldn't block the rest.
export function useWebCheck(domain) {
  const ssl = useDomainPanel('ssl-info', domain);
  const headers = useDomainPanel('security-headers', domain);
  const dnssec = useDomainPanel('dnssec', domain);
  const blocklist = useDomainPanel('blocklist', domain);
  return { ssl, headers, dnssec, blocklist, unsupported: ssl.unsupported };
}

import { useState, useEffect } from 'react';
import { webCheckApi } from '../../services/api/webCheckApi';

function isSearchPattern(domain) {
  return domain.includes('*') || domain.includes('?');
}

const CHECKS = {
  ssl: webCheckApi.getSslInfo,
  headers: webCheckApi.getSecurityHeaders,
  dnssec: webCheckApi.getDnssec,
  blocklist: webCheckApi.getBlocklist
};

function idleState() {
  return Object.keys(CHECKS).reduce((acc, key) => {
    acc[key] = { data: null, loading: false, error: null };
    return acc;
  }, {});
}

function loadingState() {
  return Object.keys(CHECKS).reduce((acc, key) => {
    acc[key] = { data: null, loading: true, error: null };
    return acc;
  }, {});
}

// The four web-check sub-checks (SSL, security headers, DNSSEC, blocklist) are fetched
// together since they're always shown as one "Web Check" panel, but each has its own
// independent loading/error state - one slow or failing check shouldn't block the rest.
export function useWebCheck(domain) {
  const [state, setState] = useState(idleState);
  const unsupported = Boolean(domain) && isSearchPattern(domain);

  useEffect(() => {
    if (!domain || isSearchPattern(domain)) {
      setState(idleState());
      return;
    }

    let ignore = false;
    setState(loadingState());

    Object.entries(CHECKS).forEach(([key, fetchFn]) => {
      fetchFn(domain)
        .then((data) => {
          if (!ignore) {
            setState((prev) => ({ ...prev, [key]: { data, loading: false, error: null } }));
          }
        })
        .catch((err) => {
          if (!ignore) {
            const message = err.response?.data?.detail || err.response?.data?.message || err.message;
            setState((prev) => ({ ...prev, [key]: { data: null, loading: false, error: message } }));
          }
        });
    });

    return () => { ignore = true; };
  }, [domain]);

  return { ...state, unsupported };
}

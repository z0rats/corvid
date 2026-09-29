import { useCallback, useEffect, useState } from 'react';
import api from '../../../../core/services/baseApi';

// One domain-finder panel's request lifecycle: `GET /api/domain/<path>/<domain>`, with
// loading/error state, stale-response suppression, and the wildcard-pattern rule (panel
// endpoints take a single plain domain - `*`/`?` search patterns are only meaningful to
// the main domain search, so a panel reports `unsupported` instead of calling its API).
//
// `auto` (default) fetches whenever `domain`/`params` change; `auto: false` waits for
// `run()` - for the slow, active panels (subfinder, host probe, site crawl).
// `notConfiguredCode` turns that backend `error_code` into `notConfigured` rather than an
// error (a missing optional API key is a setup hint, not a failure).

export interface DomainPanelOptions {
  auto?: boolean;
  params?: Record<string, string>;
  notConfiguredCode?: string;
}

export interface DomainPanelState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  notConfigured: boolean;
  unsupported: boolean;
  run: () => Promise<void>;
}

export function isSearchPattern(domain: string): boolean {
  return domain.includes('*') || domain.includes('?');
}

interface PanelRequestError {
  message?: string;
  response?: { data?: { detail?: string; message?: string; error_code?: string } };
}

export function errorMessage(err: PanelRequestError): string {
  return err?.response?.data?.detail || err?.response?.data?.message || err?.message;
}

export function useDomainPanel<T = unknown>(
  path: string,
  domain: string | null | undefined,
  { auto = true, params, notConfiguredCode }: DomainPanelOptions = {}
): DomainPanelState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notConfigured, setNotConfigured] = useState(false);
  const unsupported = Boolean(domain) && isSearchPattern(domain as string);
  const paramsKey = params ? JSON.stringify(params) : '';

  const request = useCallback(
    async (isCurrent: () => boolean) => {
      setLoading(true);
      setError(null);
      setNotConfigured(false);
      try {
        const response = await api.get(`/api/domain/${path}/${domain}`, {
          params: paramsKey ? JSON.parse(paramsKey) : undefined
        });
        if (isCurrent()) setData(response.data);
      } catch (caught) {
        const err = caught as PanelRequestError;
        if (!isCurrent()) return;
        if (notConfiguredCode && err?.response?.data?.error_code === notConfiguredCode) {
          setNotConfigured(true);
        } else {
          setError(errorMessage(err));
        }
        setData(null);
      } finally {
        if (isCurrent()) setLoading(false);
      }
    },
    [path, domain, paramsKey, notConfiguredCode]
  );

  useEffect(() => {
    if (!auto) return undefined;
    if (!domain || isSearchPattern(domain)) {
      setData(null);
      setLoading(false);
      setError(null);
      setNotConfigured(false);
      return undefined;
    }
    let ignore = false;
    request(() => !ignore);
    return () => {
      ignore = true;
    };
  }, [auto, domain, request]);

  const run = useCallback(() => request(() => true), [request]);

  return { data, loading, error, notConfigured, unsupported, run };
}

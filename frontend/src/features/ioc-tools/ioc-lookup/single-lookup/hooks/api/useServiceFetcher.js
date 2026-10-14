import { useState, useEffect, useRef } from 'react';
import { iocLookupApi } from '../../../../shared/services/api/iocLookupApi';
import { createLogger } from '../../../../../../core/utils/logger';
import { getCachedLookup, setCachedLookup } from '../../utils/lookupCache';

const logger = createLogger('ServiceFetcher');

/**
 * `bypassCache` forces a live request (an explicit re-search); otherwise a cached response from
 * this session (see utils/lookupCache.js) is reused and reported with `fromCache: true`.
 */
export function useServiceFetcher(ioc, iocType, serviceConfigEntry, onResult, bypassCache = false) {
  const [loading, setLoading] = useState(true);
  const [apiResult, setApiResult] = useState(null);
  const [displayProps, setDisplayProps] = useState({ summary: 'Loading...', tlp: 'WHITE' });

  const getDisplayDataRef = useRef(null);
  getDisplayDataRef.current = (data) => {
    if (serviceConfigEntry?.getSummaryAndTlp) {
      try {
        return serviceConfigEntry.getSummaryAndTlp(data, iocType);
      } catch (e) {
        logger.error(`Error in getSummaryAndTlp for ${serviceConfigEntry.name}:`, e);
        return { summary: 'Error processing result', tlp: 'WHITE' };
      }
    }
    return { summary: 'Data received, no summary available', tlp: 'BLUE' };
  };

  const onResultRef = useRef(onResult);
  onResultRef.current = onResult;

  useEffect(() => {
    const abortController = new AbortController();
    const getDisplayData = (data) => getDisplayDataRef.current(data);

    const reportResult = (data, display, fromCache = false) => {
      if (!onResultRef.current || !serviceConfigEntry?.key) return;
      const status = data?.notFound ? 'not_found' : data?.error ? 'error' : 'found';
      onResultRef.current(serviceConfigEntry.key, {
        service_name: serviceConfigEntry.name,
        status,
        summary: display.summary,
        tlp: display.tlp,
        data,
        fromCache,
      });
    };

    const fetchData = async () => {
      setLoading(true);
      setDisplayProps({ summary: 'Loading...', tlp: 'WHITE' });

      if (!serviceConfigEntry?.key) {
        const errorData = { error: 500, message: `No service key configured for ${serviceConfigEntry?.name}.` };
        setApiResult(errorData);
        setDisplayProps(getDisplayData(errorData));
        setLoading(false);
        return;
      }

      const cached = bypassCache ? undefined : getCachedLookup(serviceConfigEntry.key, iocType, ioc);
      if (cached !== undefined) {
        setApiResult(cached);
        const display = getDisplayData(cached);
        setDisplayProps(display);
        reportResult(cached, display, true);
        setLoading(false);
        return;
      }

      try {
        const response = await iocLookupApi.lookupSingleService(
          serviceConfigEntry.key, ioc, iocType, { signal: abortController.signal }
        );

        let data;
        if (response.error) {
          const isNotFound = response.error.toLowerCase().includes('not found');
          data = isNotFound
            ? { notFound: true, message: response.error }
            : { error: response.status, message: response.error };
        } else {
          data = response.data;
        }
        if (!data?.error) setCachedLookup(serviceConfigEntry.key, iocType, ioc, data);
        setApiResult(data);
        const display = getDisplayData(data);
        setDisplayProps(display);
        reportResult(data, display);
      } catch (error) {
        if (error.name === 'AbortError' || error.name === 'CanceledError') {
          return;
        }

        logger.error(`[${serviceConfigEntry.name}] API Error:`, error);
        const errorData = {
          error: error.response?.status || 'NETWORK_ERROR',
          message: error.response?.data?.detail || error.response?.data?.message || error.message,
          ...error.response?.data,
        };
        setApiResult(errorData);
        const display = getDisplayData(errorData);
        setDisplayProps(display);
        reportResult(errorData, display);
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => abortController.abort();
  }, [ioc, iocType, serviceConfigEntry, bypassCache]);

  return { loading, apiResult, displayProps };
}

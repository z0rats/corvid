import { useState, useEffect, useRef } from 'react';
import { iocLookupApi } from '../../../../shared/services/api/iocLookupApi';
import { createLogger } from '../../../../../../core/utils/logger';

const logger = createLogger('ServiceFetcher');

export function useServiceFetcher(ioc, iocType, serviceConfigEntry) {
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

  useEffect(() => {
    const abortController = new AbortController();
    const getDisplayData = (data) => getDisplayDataRef.current(data);

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
        setApiResult(data);
        setDisplayProps(getDisplayData(data));
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
        setDisplayProps(getDisplayData(errorData));
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => abortController.abort();
  }, [ioc, iocType, serviceConfigEntry]);

  return { loading, apiResult, displayProps };
}

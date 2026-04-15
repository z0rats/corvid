import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { determineIocType, IOC_TYPES } from '../../shared/utils/iocDefinitions';
import { getOverallTlp } from '../../shared/utils/tlpUtils';
import { SERVICE_DEFINITIONS } from '../../shared/config/serviceConfig';
import { iocLookupApi } from '../../../shared/services/api/iocLookupApi';
import { createLogger } from '../../../../../core/utils/logger';

const logger = createLogger('BulkLookupProcessor');

const initialCategorizedIocsState = Object.fromEntries(
  Object.values(IOC_TYPES).map(type => [type, []])
);

const PREFERRED_IOC_ORDER = [
  IOC_TYPES.IPV4, IOC_TYPES.IPV6, IOC_TYPES.DOMAIN, IOC_TYPES.URL,
  IOC_TYPES.MD5, IOC_TYPES.SHA1, IOC_TYPES.SHA256,
  IOC_TYPES.EMAIL, IOC_TYPES.CVE, IOC_TYPES.UNKNOWN
];

export function useBulkLookupProcessor() {
  const [categorizedIocs, setCategorizedIocs] = useState(initialCategorizedIocsState);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [processorError, setProcessorError] = useState('');

  const iocMapRef = useRef(new Map());
  const abortControllerRef = useRef(null);

  const updateIocServiceData = useCallback((iocValue, serviceName, updates) => {
    setCategorizedIocs(prev => {
      const iocToUpdate = iocMapRef.current.get(iocValue);
      if (!iocToUpdate) return prev;

      const iocType = iocToUpdate.type;
      const iocIndex = prev[iocType].findIndex(i => i.id === iocToUpdate.id);

      if (iocIndex === -1) return prev;

      const updatedIoc = {
        ...prev[iocType][iocIndex],
        services: {
          ...prev[iocType][iocIndex].services,
          [serviceName]: {
            ...prev[iocType][iocIndex].services[serviceName],
            ...updates,
          },
        },
      };

      const serviceTlps = Object.values(updatedIoc.services).map(s => s.tlp).filter(Boolean);
      updatedIoc.overallTlp = getOverallTlp(serviceTlps);

      const newTypeArray = [...prev[iocType]];
      newTypeArray[iocIndex] = updatedIoc;
      iocMapRef.current.set(iocValue, updatedIoc);

      return { ...prev, [iocType]: newTypeArray };
    });
  }, []);

  const processSSEStream = useCallback(async (stream, uniqueIocs, selectedServices, signal) => {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let completedRequests = 0;
    const totalRequests = uniqueIocs.reduce((count, ioc) => {
      const type = determineIocType(ioc);
      return count + selectedServices.filter(s => {
        const def = SERVICE_DEFINITIONS[s];
        return !def || def.supportedIocTypes.includes(type);
      }).length;
    }, 0);

    try {
    while (true) {
      if (signal?.aborted) break;
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const eventChunks = buffer.split('\n\n');
      buffer = eventChunks.pop();

      for (const chunk of eventChunks) {
        if (chunk.startsWith('data: ')) {
          completedRequests++;
          const dataStr = chunk.substring(6);
          try {
            const eventData = JSON.parse(dataStr);
            const { ioc, service, data, error } = eventData;

            if (error) {
              const isNotFound = error.toLowerCase().includes('not found');
              if (isNotFound) {
                updateIocServiceData(ioc, service, {
                  status: 'completed',
                  data: { error: true, message: error },
                  summary: 'Not found',
                  tlp: 'GREEN',
                });
              } else {
                updateIocServiceData(ioc, service, {
                  status: 'error',
                  summary: error,
                  tlp: 'WHITE',
                  error: { message: error }
                });
              }
            } else {
              const serviceDef = SERVICE_DEFINITIONS[service];
              if (serviceDef) {
                const iocType = determineIocType(ioc);
                const analysisResult = serviceDef.getSummaryAndTlp(data, iocType);
                updateIocServiceData(ioc, service, {
                  status: 'completed',
                  data: data,
                  summary: analysisResult.summary,
                  tlp: analysisResult.tlp,
                  keyMetric: analysisResult.keyMetric,
                });
              }
            }
          } catch (e) {
            logger.error('Error parsing SSE data:', e, 'Data:', dataStr);
          }
          setProgress(totalRequests > 0 ? (completedRequests / totalRequests) * 100 : 0);
        }
      }
    }
    } finally {
      reader.releaseLock();
    }
  }, [updateIocServiceData]);

  const performLookup = useCallback(async (iocsInput, selectedServices) => {
    setProcessorError('');
    if (selectedServices.length === 0) {
      setProcessorError('Please select at least one service to perform the lookup.');
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    setLoading(true);
    setProgress(0);
    iocMapRef.current.clear();

    const freshInitialCategorizedIocs = Object.fromEntries(
      Object.values(IOC_TYPES).map(type => [type, []])
    );

    const lines = iocsInput.split(/[ ,\n]+/).map(line => line.trim()).filter(Boolean);
    const uniqueIocs = Array.from(new Set(lines));

    if (uniqueIocs.length === 0) {
      setProcessorError('Please enter at least one IOC, or check input for valid formatting.');
      setLoading(false);
      return;
    }

    uniqueIocs.forEach((iocStr, index) => {
      const type = determineIocType(iocStr);
      const iocId = `${type}-${iocStr}-${crypto.randomUUID()}`;
      const services = {};
      selectedServices.forEach(serviceName => {
        const serviceDef = SERVICE_DEFINITIONS[serviceName];
        if (serviceDef && !serviceDef.supportedIocTypes.includes(type)) return;
        services[serviceName] = { status: 'idle', summary: 'Queued', tlp: 'WHITE' };
      });

      const iocObject = { id: iocId, value: iocStr, type, services, overallTlp: 'WHITE' };
      if (freshInitialCategorizedIocs[type]) {
        freshInitialCategorizedIocs[type].push(iocObject);
        iocMapRef.current.set(iocStr, iocObject);
      }
    });
    setCategorizedIocs(freshInitialCategorizedIocs);

    try {
      const stream = await iocLookupApi.bulkLookup(uniqueIocs, selectedServices);
      await processSSEStream(stream, uniqueIocs, selectedServices, signal);
    } catch (err) {
      if (signal.aborted) return;
      logger.error('SSE connection error:', err);
      setProcessorError(`Failed to connect or stream results: ${err.message}`);
    } finally {
      if (!signal.aborted) {
        setLoading(false);
        setProgress(100);
      }
    }
  }, [processSSEStream]);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const orderedIocTypes = useMemo(() => {
    const typesPresent = Object.keys(categorizedIocs).filter(type => categorizedIocs[type]?.length > 0);
    const sortedTypes = PREFERRED_IOC_ORDER.filter(type => typesPresent.includes(type));
    const otherTypes = typesPresent.filter(type => !PREFERRED_IOC_ORDER.includes(type));
    return [...sortedTypes, ...otherTypes];
  }, [categorizedIocs]);

  return {
    categorizedIocs,
    loading,
    progress,
    processorError,
    setProcessorError,
    performLookup,
    orderedIocTypes,
  };
}

import { useCallback, useRef, useMemo, useEffect } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import {
  cvss40Atom,
  CVSS40_INITIAL,
  cvss40BaseMetricsAtom,
  cvss40ThreatMetricsAtom,
  cvss40SupplementalMetricsAtom,
  cvss40EnvironmentalMetricsAtom,
  cvss40ScoresAtom,
  cvss40VectorStringAtom,
  cvss40ErrorAtom,
  cvss40LoadingAtom,
} from '../state/cvssAtoms';
import api from '../../../../core/services/baseApi';

const DEBOUNCE_DELAY = 500;

export const useCvss40 = () => {
  const setState = useSetAtom(cvss40Atom);

  const baseMetrics = useAtomValue(cvss40BaseMetricsAtom);
  const threatMetrics = useAtomValue(cvss40ThreatMetricsAtom);
  const supplementalMetrics = useAtomValue(cvss40SupplementalMetricsAtom);
  const environmentalMetrics = useAtomValue(cvss40EnvironmentalMetricsAtom);
  const scores = useAtomValue(cvss40ScoresAtom);
  const vectorString = useAtomValue(cvss40VectorStringAtom);
  const error = useAtomValue(cvss40ErrorAtom);
  const loading = useAtomValue(cvss40LoadingAtom);

  const metrics = useMemo(() => ({
    base: baseMetrics,
    threat: threatMetrics,
    supplemental: supplementalMetrics,
    environmental: environmentalMetrics,
  }), [baseMetrics, threatMetrics, supplementalMetrics, environmentalMetrics]);

  const state = useMemo(() => ({
    metrics,
    scores,
    vectorString,
    loading,
    error,
  }), [metrics, scores, vectorString, loading, error]);

  const metricsRef = useRef(metrics);
  metricsRef.current = metrics;

  const debounceTimerRef = useRef(null);

  useEffect(() => {
    return () => clearTimeout(debounceTimerRef.current);
  }, []);

  const fetchScore = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    const currentMetrics = metricsRef.current;

    try {
      const payload = {
        base_metrics: currentMetrics.base,
        threat_metrics: currentMetrics.threat,
        supplemental_metrics: currentMetrics.supplemental,
        environmental_metrics: currentMetrics.environmental,
      };

      const response = await api.post("/api/cvss/v4.0/calculate", payload);
      const scoreData = response.data;

      setState(prev => ({
        ...prev,
        vectorString: scoreData.vector_string,
        scores: {
          base_score: scoreData.base_score,
          base_severity: scoreData.base_severity,
          threat_score: scoreData.threat_score || scoreData.base_score,
          threat_severity: scoreData.threat_severity || scoreData.base_severity,
          environmental_score: scoreData.environmental_score || scoreData.base_score,
          environmental_severity: scoreData.environmental_severity || scoreData.base_severity,
        },
        loading: false,
      }));
    } catch (err) {
      const errorMessage = typeof err.response?.data?.detail === 'string'
        ? err.response.data.detail
        : err.message || "Failed to calculate CVSS 4.0 score";

      setState(prev => ({
        ...prev,
        error: errorMessage,
        loading: false,
      }));
    }
  }, [setState]);

  const scheduleFetch = useCallback(() => {
    clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(fetchScore, DEBOUNCE_DELAY);
  }, [fetchScore]);

  const updateMetric = useCallback((category, metric, value) => {
    setState(prev => ({
      ...prev,
      metrics: {
        ...prev.metrics,
        [category]: {
          ...prev.metrics[category],
          [metric]: value,
        },
      },
    }));
    scheduleFetch();
  }, [setState, scheduleFetch]);

  const updateSingleMetric = useCallback((metric, value) => {
    setState(prev => {
      const newMetrics = { ...prev.metrics };

      if (metric.startsWith('modified_')) {
        newMetrics.environmental = {
          ...newMetrics.environmental,
          [metric]: value,
        };
      } else if (['safety', 'automatable', 'recovery', 'value_density', 'vulnerability_response_effort', 'provider_urgency'].includes(metric)) {
        newMetrics.supplemental = {
          ...newMetrics.supplemental,
          [metric]: value,
        };
      } else if (metric === 'exploit_maturity') {
        newMetrics.threat = {
          ...newMetrics.threat,
          [metric]: value,
        };
      } else {
        newMetrics.base = {
          ...newMetrics.base,
          [metric]: value,
        };
      }

      return {
        ...prev,
        metrics: newMetrics,
      };
    });
    scheduleFetch();
  }, [setState, scheduleFetch]);

  const resetState = useCallback(() => {
    clearTimeout(debounceTimerRef.current);
    setState(CVSS40_INITIAL);
  }, [setState]);

  return {
    state,
    updateMetric,
    updateSingleMetric,
    resetState,
  };
};

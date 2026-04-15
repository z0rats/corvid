import { useCallback, useRef, useMemo, useEffect } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import {
  cvss31Atom,
  CVSS31_INITIAL,
  cvss31BaseMetricsAtom,
  cvss31TemporalMetricsAtom,
  cvss31EnvironmentalMetricsAtom,
  cvss31ScoresAtom,
  cvss31VectorStringAtom,
  cvss31ErrorAtom,
  cvss31LoadingAtom,
} from '../state/cvssAtoms';
import { calculateCVSS31 } from '../utils/cvss31Calculator';
import api from '../../../../core/services/baseApi';

const DEBOUNCE_DELAY = 1000;

export const useCvss31 = () => {
  const setState = useSetAtom(cvss31Atom);

  const baseMetrics = useAtomValue(cvss31BaseMetricsAtom);
  const temporalMetrics = useAtomValue(cvss31TemporalMetricsAtom);
  const environmentalMetrics = useAtomValue(cvss31EnvironmentalMetricsAtom);
  const scores = useAtomValue(cvss31ScoresAtom);
  const vectorString = useAtomValue(cvss31VectorStringAtom);
  const error = useAtomValue(cvss31ErrorAtom);
  const loading = useAtomValue(cvss31LoadingAtom);

  const metrics = useMemo(() => ({
    base: baseMetrics,
    temporal: temporalMetrics,
    environmental: environmentalMetrics,
  }), [baseMetrics, temporalMetrics, environmentalMetrics]);

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

  const fetchVectorString = useCallback(async () => {
    const currentMetrics = metricsRef.current;
    try {
      const environmentalPayload = {
        confidentiality_requirement: currentMetrics.environmental.confidentialityRequirement,
        integrity_requirement: currentMetrics.environmental.integrityRequirement,
        availability_requirement: currentMetrics.environmental.availabilityRequirement,
      };

      if (currentMetrics.environmental.modifiedAttackVector !== null) {
        environmentalPayload.modified_attack_vector = currentMetrics.environmental.modifiedAttackVector;
      }
      if (currentMetrics.environmental.modifiedAttackComplexity !== null) {
        environmentalPayload.modified_attack_complexity = currentMetrics.environmental.modifiedAttackComplexity;
      }
      if (currentMetrics.environmental.modifiedPrivilegesRequired !== null) {
        environmentalPayload.modified_privileges_required = currentMetrics.environmental.modifiedPrivilegesRequired;
      }
      if (currentMetrics.environmental.modifiedUserInteraction !== null) {
        environmentalPayload.modified_user_interaction = currentMetrics.environmental.modifiedUserInteraction;
      }
      if (currentMetrics.environmental.modifiedScope !== null) {
        environmentalPayload.modified_scope = currentMetrics.environmental.modifiedScope;
      }
      if (currentMetrics.environmental.modifiedConfidentialityImpact !== null) {
        environmentalPayload.modified_confidentiality_impact = currentMetrics.environmental.modifiedConfidentialityImpact;
      }
      if (currentMetrics.environmental.modifiedIntegrityImpact !== null) {
        environmentalPayload.modified_integrity_impact = currentMetrics.environmental.modifiedIntegrityImpact;
      }
      if (currentMetrics.environmental.modifiedAvailabilityImpact !== null) {
        environmentalPayload.modified_availability_impact = currentMetrics.environmental.modifiedAvailabilityImpact;
      }

      const payload = {
        base_metrics: {
          attack_vector: currentMetrics.base.attackVector,
          attack_complexity: currentMetrics.base.attackComplexity,
          privileges_required: currentMetrics.base.privilegesRequired,
          user_interaction: currentMetrics.base.userInteraction,
          scope: currentMetrics.base.scope,
          confidentiality_impact: currentMetrics.base.confidentialityImpact,
          integrity_impact: currentMetrics.base.integrityImpact,
          availability_impact: currentMetrics.base.availabilityImpact,
        },
        temporal_metrics: {
          exploit_code_maturity: currentMetrics.temporal.exploitCodeMaturity,
          remediation_level: currentMetrics.temporal.remediationLevel,
          report_confidence: currentMetrics.temporal.reportConfidence,
        },
        environmental_metrics: environmentalPayload,
      };

      const response = await api.post("/api/cvss/v3.1/calculate", payload);
      const responseScores = response.data;

      setState(prev => ({
        ...prev,
        vectorString: responseScores.vector_string,
        error: null,
      }));
    } catch (err) {
      const errorMessage = typeof err.response?.data?.detail === 'string'
        ? err.response.data.detail
        : err.message || "Failed to fetch CVSS 3.1 vector string";

      setState(prev => ({
        ...prev,
        error: errorMessage,
      }));
    }
  }, [setState]);

  const scheduleFetch = useCallback(() => {
    clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(fetchVectorString, DEBOUNCE_DELAY);
  }, [fetchVectorString]);

  const updateMetric = useCallback((category, metric, value) => {
    setState(prev => {
      const newMetrics = {
        ...prev.metrics,
        [category]: {
          ...prev.metrics[category],
          [metric]: value,
        },
      };

      const calculatedScores = calculateCVSS31(newMetrics);

      return {
        ...prev,
        metrics: newMetrics,
        scores: calculatedScores,
      };
    });
    scheduleFetch();
  }, [setState, scheduleFetch]);

  const resetState = useCallback(() => {
    clearTimeout(debounceTimerRef.current);
    setState(CVSS31_INITIAL);
  }, [setState]);

  return {
    state,
    updateMetric,
    resetState,
  };
};
